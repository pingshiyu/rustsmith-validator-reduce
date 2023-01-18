import argparse
from pathlib import Path

from mutation_test.killing_ground.rustsmith import (
    try_killing_with, 
    KillingGroundSettings,
    MUTATED_RUSTC_PATH, 
    DEFAULT_OUT_DIR,
    TEMPLATE_SCRIPT_PATH, 
    _REDUCTION_FOLDER_NAME
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.killing_ground.pre_generated",
        description="Use pre-generated files to massacre mutants.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    killing_settings = parser.add_argument_group("Murder Settings")
    # mutants, time per mutant, use extra quota on unkillable mutants, desired level of killing, number of RustSmith tests to generate each cycle
    killing_settings.add_argument(
        "-m",
        "--mutant",
        type=int,
        required=True,
        help="Target mutant to kill with your files",
    )
    killing_settings.add_argument("-t", "--tests-root", type=Path, required=True,
                                  help="Path to folder containing your killer test cases.")

    # do a bit more parsing once inputs are specified
    args = parser.parse_args()

    return args

def main():
    args = parse_args()

    reduction_folder = DEFAULT_OUT_DIR / _REDUCTION_FOLDER_NAME
    (reduction_folder).mkdir(parents=True, exist_ok=True)

    results = try_killing_with(args.tests_root, args.mutant, reduction_folder)
    print(results)

if __name__ == '__main__':
    main()