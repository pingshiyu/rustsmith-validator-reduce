"""
cmd line interface to check if the {rust-script, compilers} test case demonstrates mutation-differential on mutation x.
"""
from reducer.comparison import CompilerConfig, TestCase, ReductionEnv, prepare_reduce_folder

from pathlib import Path
import subprocess
import argparse
import shutil
from multiprocessing import Pool
from enum import Enum, auto
from dataclasses import dataclass

MUTATED_RUSTC_PATH = "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"
TEMPLATE_SCRIPT_PATH = Path("reducer/shell-script-templates/triggers_bug.sh")
DEFAULT_REDUCE_ROOT = Path("reducer/reduce/mutations/")
MAX_MUTANT = 380


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
    mutation_config.add_argument("--panic-kills-interesting", action="store_true", default=False,
                                 help="Are panic kills interesting to the reducer?")
    mutation_config.add_argument("--binary-error-uninteresting", action="store_true", default=False,
                                 help="Are compiler binary erroring uninteresting to the reducer?")

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

class Detection(Enum):
    UNKNOWN = 0
    DETECTED = auto()
    UNDETECTED = auto() # bug not present
    PANIC = auto()
    COMPILE_TIMEOUT = auto()
    BINARY_ERRORS = auto()
    BINARY_TIMEOUT = auto()

def detection(return_code: int) -> Detection:
    if return_code == 0:
        return Detection.DETECTED
    elif return_code == 1:
        return Detection.UNDETECTED
    elif return_code == 2:
        return Detection.PANIC
    elif return_code == 3:
        return Detection.BINARY_ERRORS
    elif return_code == 4:
        return Detection.BINARY_TIMEOUT
    else:
        return Detection.UNKNOWN

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
        return detection(result.returncode)
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
    panic_kill_is_interesting: bool
    bin_err_is_interesting: bool
    bin_timeout_is_interesting: bool
    reduce_root: Path
    template_script_path: Path
    keep_folder: bool

def get_context(args: argparse.Namespace) -> TestContext:
    return TestContext(args.compiler, args.input_path, args.input_args_path,
                       args.panic_kills_interesting, 
                       not args.binary_error_uninteresting, not args.binary_error_uninteresting, 
                       args.reduce_root, args.template_script, args.keep)

def check_single(env: TestContext, mutant: int) -> Detection:
    # create a test case using the test script, compiler, and mutation settings.
    test_case = TestCase(
        CompilerConfig("", "0", 0, env.compiler), 
        CompilerConfig("", "0", mutant, env.compiler), 
        env.input_path, 
        env.input_args_path,
        panic_kill_is_interesting=env.panic_kill_is_interesting,
        bin_err_is_interesting=env.bin_err_is_interesting,
        bin_timeout_is_interesting=env.bin_timeout_is_interesting
    )
    
    return difference_detected(
        test_case, 
        ReductionEnv(env.reduce_root, env.template_script_path), 
        keep=env.keep_folder
    )

def check_all(env: TestContext, min_mutant: int, max_mutant: int, jobs: int = 8) -> list[tuple[int, Detection]]:
    """
    Check if any of [min_mutant, max_mutant] mutants results in different code on the
    test case `env`
    """
    mutants_detected = []
    with Pool(processes=jobs) as p:
        mutants = list(range(min_mutant, max_mutant+1))
        async_results = [p.apply_async(check_single, (env, m)) for m in mutants]

        # get the results
        for m, result in zip(mutants, async_results):
            detected = result.get()

            if (detected != Detection.UNDETECTED) and (detected != Detection.UNKNOWN):
                mutants_detected.append((m, detected))

    return mutants_detected

def main() -> None:
    args = parse_args()
    # print(args)

    env = get_context(args)

    if args.try_all:
        print(f"mutants detected by {env.input_path}:", check_all(env, args.mutation, args.max_mutation))
    else:
        print(f"mutant {args.mutation} detected by {env.input_path}:", check_single(env, args.mutation))

if __name__ == '__main__':
    main()
