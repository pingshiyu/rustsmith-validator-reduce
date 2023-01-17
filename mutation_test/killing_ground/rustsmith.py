import argparse
from pathlib import Path

RUSTSMITH_ROOT = Path("/home/jacob/Projects/rustsmith")
RUSTSMITH_PATH = RUSTSMITH_ROOT / "rustsmith/bin/rustsmith"
DEFAULT_OUT_DIR = RUSTSMITH_ROOT / "rustsmith-validator-reduce/mutation_test/killing_ground/out"

_RUSTSMITH_FOLDER_NAME = "_rustsmith"
RUSTSMITH_OUT_DIR = DEFAULT_OUT_DIR / _RUSTSMITH_FOLDER_NAME

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.round_robin.rustsmith",
        description="Using RustSmith to massacre mutants.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    killing_settings = parser.add_argument_group('Killing Experiment Settings')
    # mutants, time per mutant, use extra quota on unkillable mutants, desired level of killing, number of RustSmith tests to generate each cycle 
    killing_settings.add_argument("-m", "--mutants", type=int, nargs='+', required=True,
                                  help="Kill list of mutants. Separated by space. E.g. 5 7 93 95 96 100 101")
    killing_settings.add_argument("--minutes-per-mutant", type=float, default=5,
                                  help="Time to spend on each mutant, in minutes.")
    killing_settings.add_argument("--use-spare-quota", action="store_true",
                                  help="Use extra quota for killing mutants which survived the allocated time?")
    killing_settings.add_argument("--level" ,type=str, choices=["panic", "run-error", "run-diff", "full"], default="full", 
                                  help=("Level to which the mutant can be considered fully killed. Levels are: "
                                        "Reached < Pacic; Reached < Binary-Diff < Run-Error/Timeout < Run-Difference. "
                                        "After mutating the compiler, consider killed if compile(m)(test): "
                                        "panic => compiler panics; run-error => generated binary now errors/timeouts; "
                                        "run-diff => generated binary runs but produce different results."))
    killing_settings.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                                  help="Location to save the test cases found to kill mutants (and killing strength).")
    killing_settings.add_argument("--cases-per-cycle", type=int, default=25,
                                  help="How many test cases to generate per generate-kill cycle.")
    killing_settings.add_argument("--rustsmith-path", type=Path, default=RUSTSMITH_PATH,
                                  help="Path to the RustSmith executable.")

    # do a bit more parsing once inputs are specified
    args = parser.parse_args()

    return args

def _prepare_killing_ground(mutants: list[int], ground_root: Path):
    ground_root.mkdir(parents=True, exist_ok=True)
    (ground_root / _RUSTSMITH_FOLDER_NAME).mkdir(exist_ok=True)
    for mutant in mutants:
        (ground_root / str(mutant)).mkdir(exist_ok=True)

def attempt_murder(mutant: int, timeout: float):
    """
    Attempt to kill `mutant` within time limit `timeout`.
    """
    # generate and kill loop
    pass

def main():
    args = parse_args()
    print(args)

    # prepare directories structure
    _prepare_killing_ground(args.mutants, args.out_dir)

    # try to kill each mutant
    

if __name__ == '__main__':
    main()