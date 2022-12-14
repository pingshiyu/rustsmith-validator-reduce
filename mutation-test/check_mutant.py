"""
cmd line interface to check if the {rust-script, compilers} test case demonstrates mutation-differential on mutation x.
"""
from reducer.comparison import CompilerConfig, TestCase, ReductionEnv, prepare_reduce_folder

from pathlib import Path
import subprocess
import argparse
import shutil

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation-test.check_mutant",
        description="Checks files against mutations"
    )

    test_case_config = parser.add_argument_group('Test Case Specification')
    test_case_config.add_argument("-i", "--input-path", type=Path, required=True,
                            help="Path input script triggering the test_case.")
    test_case_config.add_argument("-a", "--input-args-path", type=Path, required=False,
                            help="Path to the cmd args of the input test case.")

    compiler_config = test_case_config.add_mutually_exclusive_group()
    mutated_rustc_location = "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"
    compiler_config.add_argument("-c", "--compiler", type=str,
                                 default=mutated_rustc_location,
                                 help="Location of compiler to use")
    compiler_config.add_argument("--use-default-compiler", action="store_const", dest="compiler",
                                 const="rustc",
                                 help="Use the default rustc compiler")
    compiler_config.add_argument("--use-mutation-compiler", action="store_const", dest="compiler",
                                 const=mutated_rustc_location,
                                 help="Use the rustc compiler with mutations built in")

    mutation_config = parser.add_argument_group("Mutation Settings")
    mutation_config.add_argument("-m", "--mutation", type=int, required=True,
                                 help="Type of mutation to compare (against no mutations)")
    mutation_config.add_argument("--try-all", action="store_true", default=False,
                        help="Try all mutatnts in range [mutation, max_mutantion]?")
    mutation_config.add_argument("-mm", "--max-mutation", type=int, default=380,
                                 help="Which mutant number to try up to?")

    parser.add_argument("--reduce-root", type=Path, required=False,
                        default="reducer/reduce",
                        help="Place to put the reduce folder")
    parser.add_argument("--template-script", type=Path, required=False,
                        default="reducer/shell-script-templates/triggers_bug.sh",
                        help="Place to put the reduce folder")
    parser.add_argument("--keep", action="store_true", default=False,
                        help="Keep created temp reduction folder")    

    # do a bit more parsing once inputs are specified
    args = parser.parse_args()

    # default: if input-args doesn't exist, assume it's the .txt file with the same name as
    # `input_path`
    if not args.input_args_path:
        input_name = args.input_path.name.rsplit('.', maxsplit=1)[0]
        args.input_args_path = args.input_path.parent / f"{input_name}.txt"

    return args

def difference_detected(
    test_case: TestCase,
    env: ReductionEnv,
    keep: bool = False) -> bool:
    """
    Checks if the test_case is able to detect the `mutant`. Returns true iff difference exists
    """
    reduction_folder = prepare_reduce_folder(test_case, env)

    # run the interestingness script to check if test_case exists
    result = subprocess.run("./interesting.sh", cwd=reduction_folder)

    # cleanup folder created
    if not keep:
        shutil.rmtree(reduction_folder)

    return result.returncode == 0

def check_single(args: argparse.Namespace) -> bool:
    # create a test case using the test script, compiler, and mutation settings.
    test_case = TestCase(
        CompilerConfig("", "0", 0, args.compiler), 
        CompilerConfig("", "0", args.mutation, args.compiler), 
        args.input_path, 
        args.input_args_path
    )
    
    return difference_detected(
        test_case, 
        ReductionEnv(args.reduce_root, args.template_script), 
        keep=args.keep
    )

def check_all(args: argparse.Namespace, min_mutant: int, max_mutant: int) -> list[int]:
    """
    Check if any of [args.mutation, max_mutant) mutants results in different code on the
    test case {args.input_path, args.input_args_path} 
    """
    mutants_detected = []

    for m in range(args.mutation, max_mutant+1):
        # create a test case using the test script, compiler, and mutation settings.
        test_case = TestCase(
            CompilerConfig("", "0", 0, args.compiler), 
            CompilerConfig("", "0", m, args.compiler), 
            args.input_path, 
            args.input_args_path
        )
        
        detected = difference_detected(
            test_case, 
            ReductionEnv(args.reduce_root, args.template_script), 
            keep=args.keep
        )
        if detected:
            mutants_detected.append(m)

    return mutants_detected

def main() -> None:
    args = parse_args()
    # print(args)

    if args.try_all:
        print("mutants triggered:", check_all(args, args.mutation, args.max_mutation))
    else:
        check_single(args)

    # mutations [12, 18, 20, 28, 43] killed by `mutation-test/tests/outRust-12/file0/file0.rs`

if __name__ == '__main__':
    main()
