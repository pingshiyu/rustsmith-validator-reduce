"""
cmd line interface to check if the {rust-script, compilers} test case demonstrates mutation-differential on mutation x.
"""
from reducer.comparison import CompilerConfig, TestCase, ReductionEnv, prepare_reduce_folder
from mutation_test.settings import MUTATED_RUSTC_PATH, MAX_MUTANT, DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, Detection, return_code_to_detection, get_kill_return_values

from pathlib import Path
import subprocess
import argparse
import shutil
from multiprocessing import Pool
from dataclasses import dataclass

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.mutation_coverage",
        description="Computes mutation coverage of test cases"
    )

    test_case_config = parser.add_argument_group('Test Case Specification')
    test_case_config.add_argument("-i", "--input-path", type=Path, required=True,
                            help="Path input script triggering the test_case.")
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

    # default: if input-args doesn't exist, assume it's the .txt file with the same name as
    # `input_path`
    if not args.input_args_path:
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

@dataclass
class TestContext:
    compiler: str
    input_path: Path
    input_args_path: Path
    reduce_root: Path
    template_script_path: Path
    keep_folder: bool
    panic_kill_is_interesting: bool      # TODO: do something with these values here
    bin_diff_is_interesting: bool        # TODO: do something with these values here
    output_error_is_interesting: bool    # TODO: do something with these values here

def _get_context(args: argparse.Namespace) -> TestContext:
    return TestContext(args.compiler, args.input_path, args.input_args_path,
                       args.reduce_root, args.template_script, args.keep,
                       args.panic_kill_interesting, args.bin_diff_interesting, args.output_error_interesting)

def check_single(env: TestContext, mutant: int) -> Detection:
    # create a test case using the test script, compiler, and mutation settings.
    test_case = TestCase(
        CompilerConfig("", "-Zmir-opt-level=4 -Copt-level=1", 0,      env.compiler), 
        CompilerConfig("", "-Zmir-opt-level=4 -Copt-level=1", mutant, env.compiler), 
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
    env: TestContext, 
    min_mutant: int, max_mutant: int, 
    jobs: int = 8, 
    timeout_early_stop_pct: float = 0.50,
    timeout_check_from: int = 10) -> list[tuple[int, Detection]]:
    """
    Check if any of [min_mutant, max_mutant] mutants results in different code on the
    test case `env`
    """
    mutants_detected = []
    with Pool(processes=jobs) as p:
        mutants = list(range(min_mutant, max_mutant+1))
        async_results = [p.apply_async(check_single, (env, m)) for m in mutants]

        # keep running tally of % of failed cases. stop early if we have too many timeouts
        timeouts = 0

        # get the results
        for m, result in zip(mutants, async_results):
            detected = result.get()

            if (detected == Detection.COMPILE_TIMEOUT):
                timeouts += 1
                
                # calculate % of failed here. stop early if greater % than threshold
                if ((m+1) > timeout_check_from) and ((timeouts / (m+1)) > timeout_early_stop_pct):
                    mutants_detected.append((-1, Detection.UNKNOWN)) # indicate early stop
                    break

            if (detected != Detection.UNDETECTED) and (detected != Detection.UNKNOWN):
                mutants_detected.append((m, detected))

    return mutants_detected

def main() -> None:
    args = parse_args()
    # print(args)

    env = _get_context(args)

    if args.try_all:
        print(f"mutants detected by {env.input_path}:", check_all(env, args.mutation, args.max_mutation))
    else:
        print(f"mutant {args.mutation} detected by {env.input_path}:", check_single(env, args.mutation))

if __name__ == '__main__':
    main()
