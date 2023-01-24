"""
cmd line interface to check if the {rust-script, compilers} test case demonstrates mutation-differential on mutation x.
"""
from reducer.comparison import CompilerConfig, TestCase, ReductionEnv, prepare_reduce_folder
from mutation_test.settings import MUTATED_RUSTC_PATH, MAX_MUTANT, DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, MIR_COMPILE_FLAGS, Detection, return_code_to_detection, get_kill_return_values

from pathlib import Path
import subprocess
import argparse
import shutil
from multiprocessing import Pool
from dataclasses import dataclass
from typing import Optional
from warnings import warn

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.mutation_coverage",
        description="Computes mutation coverage of test cases"
    )

    test_case_config = parser.add_argument_group('Test Case Specification')
    test_case_config.add_argument("-i", "--input-path", type=Path, required=True,
                                  help="Path input script triggering the test_case.")
    test_case_config.add_argument("--no-input-args", action="store_true",
                                  help="This file does not have any input args.")
    test_case_config.add_argument("-a", "--input-args-path", type=Path, required=False,
                                  help="Path to the cmd args of the input test case.")
    

    compiler_config = test_case_config.add_mutually_exclusive_group()
    compiler_config.add_argument("-c", "--compiler", type=str,
                                 default=MUTATED_RUSTC_PATH,
                                 help="Location of compiler to use")
    compiler_config.add_argument("--use-default-compiler", action="store_const", dest="compiler",
                                 const="rustc",
                                 help="Use the default rustc compiler")
    compiler_config.add_argument("--use-mutation-compiler", action="store_const", dest="compiler",
                                 const=MUTATED_RUSTC_PATH,
                                 help="Use the rustc compiler with mutations built in")

    mutation_config = parser.add_argument_group("Mutation Settings")
    mutation_config.add_argument("-m", "--mutation", type=int, required=True,
                                 help="Type of mutation to compare (against no mutations)")
    mutation_config.add_argument("--try-all", action="store_true", default=False,
                        help="Try all mutatnts in range [mutation, max_mutantion]?")
    mutation_config.add_argument("-mm", "--max-mutation", type=int, default=MAX_MUTANT,
                                 help="Which mutant number to try up to?")
    mutation_config.add_argument("--panic-kill-interesting", action="store_true", default=False,
                                 help="Are panic kills interesting to the reducer?")
    mutation_config.add_argument("--bin-diff-interesting", action="store_true", default=False,
                                 help="Is the binary being different (but same output when ran) interesting to the reducer?")
    mutation_config.add_argument("--output-error-interesting", action="store_true", default=False,
                                 help="Are output binary errors/timeouts interesting to the reducer?")

    parser.add_argument("--reduce-root", type=Path, required=False,
                        default=DEFAULT_REDUCE_ROOT,
                        help="Place to put the reduce folder")
    parser.add_argument("--template-script", type=Path, required=False,
                        default=TEMPLATE_SCRIPT_PATH,
                        help="Place to put the reduce folder")
    parser.add_argument("--keep", action="store_true", default=False,
                        help="Keep created temp reduction folder")
    

    # do a bit more parsing once inputs are specified
    args = parser.parse_args()

    # default: if input-args doesn't exist, and input args are expected, assume it's the .txt 
    # file with the same name as `input_path`
    if (not args.no_input_args) and (not args.input_args_path):
        args.input_args_path = get_default_args_path(args.input_path)

    return args

def get_default_args_path(test_path: Path) -> Path:
    test_name = test_path.name.rsplit('.', maxsplit=1)[0]
    return test_path.parent / f"{test_name}.txt"

def difference_detected(
    test_case: TestCase,
    env: ReductionEnv,
    keep: bool = False,
    timeout: int = 30) -> Detection:
    """
    Checks if the test_case is able to detect the `mutant`. Returns true iff difference exists
    """
    reduction_folder = prepare_reduce_folder(test_case, env)

    # run the interestingness script to check if test_case exists
    try:
        result = subprocess.run(
            "./interesting.sh", cwd=reduction_folder, 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=timeout
        )
        return return_code_to_detection(result.returncode)
    except subprocess.TimeoutExpired:
        return Detection.COMPILE_TIMEOUT
    finally:
        # cleanup folder created
        if not keep:
            shutil.rmtree(reduction_folder)

@dataclass(frozen=True, eq=True)
class MutationContext:
    compiler: str
    mutant: int
    input_path: Path
    input_args_path: Optional[Path]
    reduce_root: Path
    template_script_path: Path
    keep_folder: bool
    panic_kill_is_interesting: bool
    bin_diff_is_interesting: bool
    output_error_is_interesting: bool

def _get_contexts(args: argparse.Namespace) -> set[MutationContext] | MutationContext:
    """
    Returns a list of contexts iff `args.try_all == True`.
    """
    if args.try_all:
        contexts = set()
        for m in range(args.mutation, args.max_mutation):
            context = MutationContext(args.compiler, m, args.input_path, args.input_args_path,
                                  args.reduce_root, args.template_script, args.keep,
                                  args.panic_kill_interesting, args.bin_diff_interesting, args.output_error_interesting)
            contexts.add(context)
        return contexts
    else:
        return MutationContext(args.compiler, args.mutation, args.input_path, args.input_args_path,
                           args.reduce_root, args.template_script, args.keep,
                           args.panic_kill_interesting, args.bin_diff_interesting, args.output_error_interesting)

def check_single(env: MutationContext) -> Detection:
    # create a test case using the test script, compiler, and mutation settings.
    test_case = TestCase(
        CompilerConfig("", MIR_COMPILE_FLAGS,          0, env.compiler), 
        CompilerConfig("", MIR_COMPILE_FLAGS, env.mutant, env.compiler), 
        env.input_path, 
        env.input_args_path,
    )

    return_values = get_kill_return_values()
    if env.panic_kill_is_interesting:
        return_values["compile_panic_return"] = 0
        return_values["compile_timeout_return"] = 0
    if env.bin_diff_is_interesting:
        return_values["binary_difference_return"] = 0
    if env.output_error_is_interesting:
        return_values["output_timeout_return"] = 0
        return_values["output_err_return"] = 0
    # default: output_diff_return is interesting
    
    return difference_detected(
        test_case, 
        ReductionEnv(return_values, env.reduce_root, env.template_script_path), 
        keep=env.keep_folder
    )

def check_all(
    contexts: set[MutationContext], 
    jobs: int = 8,
    timeout_early_stop_pct: float = 0.75,
    timeout_check_from: int = 20) -> dict[MutationContext, Detection]:
    """
    Evaluate each context in `contexts` for how strongly the mutant is killed.
    Returns the result of the test. Optionally stop early if the majority of the tests
    were found to be of type `Detection.COMPILE_TIMEOUT`
    """
    test_results = {}
    with Pool(processes=jobs) as p:
        async_results = [p.apply_async(check_single, [context]) for context in contexts]

        # keep running tally of % of failed cases. stop early if we have too many timeouts
        n_timeouts = 0
        n_evaluated = 0

        # get the results       
        for context, result in zip(contexts, async_results):
            n_evaluated += 1
            detected = result.get()
            test_results[context] = detected

            if detected == Detection.UNKNOWN:
                warn(f"Unknown result from: {context}")

            if (detected == Detection.COMPILE_TIMEOUT):
                n_timeouts += 1
                
                # calculate % of failed here. stop early if greater % than threshold
                timeout_rate = n_timeouts / n_evaluated
                if (n_evaluated > timeout_check_from) and (timeout_rate > timeout_early_stop_pct):
                    test_results[context] = Detection.COMPILE_TIMEOUT_STOPPED_EARLY # indicate early stop
                    warn(f"Stopping early on {n_evaluated} due to timeout rate of {timeout_rate*100}%: {context}")
                    break
    return test_results

def main() -> None:
    args = parse_args()
    # print(args)

    envs = _get_contexts(args)

    if args.try_all:
        results = check_all(envs)
        mutation_results = [(mut_test.mutant, detection) for mut_test, detection in results.items()
                            if (detection != Detection.UNDETECTED) and (detection != Detection.UNKNOWN)]
        print(f"mutants detected by {args.input_path}:", mutation_results)
    else:
        print(f"mutant {args.mutation} detected by {args.input_path}:", check_single(envs))

if __name__ == '__main__':
    main()
