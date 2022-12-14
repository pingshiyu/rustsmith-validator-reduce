"""
cmd line interface to check if the {rust-script, compilers} bug report 
demonstrates mutation-differential on mutation x.
"""
from reducer.comparison import BugConfig, Bug, prepare_reduce_folder

from pathlib import Path
import subprocess
import argparse
import shutil

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation-test.check_mutant",
        description="Checks files against mutations"
    )

    bug_config = parser.add_argument_group('Bug Configuration')
    bug_config.add_argument("-i", "--input-path", type=Path, required=True,
                            help="Path input script triggering the bug.")
    bug_config.add_argument("-a", "--input-args-path", type=Path, required=False,
                            help="Path to the cmd args of the input test case.")

    compiler_config = bug_config.add_mutually_exclusive_group()
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

def main() -> subprocess.CompletedProcess:
    args = parse_args()
    # print(args)

    # create a test case using the buggy script, compiler, and mutation settings.
    bug = Bug(
        BugConfig("", "0", 0, args.compiler), 
        BugConfig("", "0", args.mutation, args.compiler), 
        args.input_path, 
        args.input_args_path
    )
    reduction_folder = prepare_reduce_folder(bug, args.reduce_root, args.template_script)

    # run the interestingness script to check if bug exists
    result = subprocess.run("./interesting.sh", cwd=reduction_folder)

    # cleanup folder created
    if not args.keep:
        shutil.rmtree(reduction_folder)

    return result

if __name__ == '__main__':
    main()
