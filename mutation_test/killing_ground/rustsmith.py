import argparse
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
import subprocess
from multiprocessing import Pool
import glob

from utils import timeout, random_str
from mutation_test.mutation_coverage import TestContext, check_single
from mutation_test.settings import Detection

RUSTSMITH_ROOT = Path("/home/jacob/Projects/rustsmith")
RUSTSMITH_PATH = RUSTSMITH_ROOT / "rustsmith/bin/rustsmith"
DEFAULT_OUT_DIR = (
    RUSTSMITH_ROOT / "rustsmith-validator-reduce/mutation_test/killing_ground/out"
)

_RUSTSMITH_FOLDER_NAME = "_rustsmith"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.round_robin.rustsmith",
        description="Using RustSmith to massacre mutants.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    killing_settings = parser.add_argument_group("Killing Experiment Settings")
    # mutants, time per mutant, use extra quota on unkillable mutants, desired level of killing, number of RustSmith tests to generate each cycle
    killing_settings.add_argument(
        "-m",
        "--mutants",
        type=int,
        nargs="+",
        required=True,
        help="Kill list of mutants. Separated by space. E.g. 5 7 93 95 96 100 101",
    )
    killing_settings.add_argument(
        "--minutes-per-mutant",
        type=float,
        default=5,
        help="Time to spend on each mutant, in minutes.",
    )
    killing_settings.add_argument(
        "--use-spare-quota",
        action="store_true",
        help="Use extra quota for killing mutants which survived the allocated time?",
    )
    killing_settings.add_argument(
        "--level",
        type=str,
        choices=["panic", "run-error", "run-diff", "full"],
        default="full",
        help=(
            "Level to which the mutant can be considered fully killed. Levels are: "
            "Reached < Pacic; Reached < Binary-Diff < Run-Error/Timeout < Run-Difference. "
            "After mutating the compiler, consider killed if compile(m)(test): "
            "panic => compiler panics; run-error => generated binary now errors/timeouts; "
            "run-diff => generated binary runs but produce different results."
        ),
    )
    killing_settings.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Location to save the test cases found to kill mutants (and killing strength).",
    )
    killing_settings.add_argument(
        "--cases-per-cycle",
        type=int,
        default=25,
        help="How many test cases to generate per generate-kill cycle.",
    )
    killing_settings.add_argument(
        "--rustsmith-path",
        type=Path,
        default=RUSTSMITH_PATH,
        help="Path to the RustSmith executable.",
    )
    killing_settings.add_argument(
        "--threads",
        type=int,
        default=8,
        help="Threads to dedicate for generation/killing of mutants.",
    )

    # do a bit more parsing once inputs are specified
    args = parser.parse_args()

    return args


class KillingLevel(Enum):
    UNKNOWN = auto()
    FULL = auto()
    RUN_DIFF = auto()
    RUN_ERROR = auto()
    PANIC = auto()


def get_killing_level(level: str) -> KillingLevel:
    if level == "full":
        return KillingLevel.FULL
    elif level == "run-diff":
        return KillingLevel.RUN_DIFF
    elif level == "run-error":
        return KillingLevel.RUN_ERROR
    elif level == "panic":
        return KillingLevel.PANIC
    else:
        return KillingLevel.UNKNOWN


def sufficient_for_level(level: KillingLevel, detection_types: set[Detection]) -> bool:
    if level == KillingLevel.FULL:
        return sufficient_for_level(
            KillingLevel.RUN_DIFF, detection_types
        ) and sufficient_for_level(KillingLevel.PANIC, detection_types)
    elif level == KillingLevel.RUN_DIFF:
        return Detection.OUTPUT_DIFFERENCE in detection_types
    elif level == KillingLevel.RUN_ERROR:
        return (
            sufficient_for_level(KillingLevel.RUN_DIFF, detection_types)
            or (Detection.OUTPUT_ERRORS in detection_types)
            or (Detection.OUTPUT_TIMEOUT in detection_types)
        )
    elif level == KillingLevel.PANIC:
        return (Detection.COMPILE_PANIC in detection_types) or (
            Detection.COMPILE_TIMEOUT in detection_types
        )
    else:
        return False


@dataclass
class KillingGroundSettings:
    minutes_per_mutant: float
    level: KillingLevel
    use_spare_quota: bool = False
    rustsmiths_per_cycle: int = 25
    rustsmith_path: Path = RUSTSMITH_PATH
    out_dir: Path = DEFAULT_OUT_DIR
    threads: int = 8


def _prepare_killing_ground(mutants: list[int], ground_root: Path):
    ground_root.mkdir(parents=True, exist_ok=True)
    (ground_root / _RUSTSMITH_FOLDER_NAME).mkdir(exist_ok=True)
    for mutant in mutants:
        (ground_root / str(mutant)).mkdir(exist_ok=True)


def try_killing_with(
    cases_root: Path, mutant: int, ground: KillingGroundSettings
) -> dict[Path, Detection]:
    """
    Try kill mutants using the generated cases in `cases_root`
    Returns a mapping of how each file did to kill the mutant.
    """
    pass


def attempt_murder(mutant: int, ground: KillingGroundSettings) -> None:
    """
    Attempt to kill `mutant` within time limit `timeout`.
    """
    coverage: dict[Detection, Path] = {}

    with timeout(ground.minutes_per_mutant * 60) as timer:
        while True:
            if timer.timed_out:
                return

            # generate test cases
            rustsmith_cases_folder = ground.out_dir / _RUSTSMITH_FOLDER_NAME
            rustsmith_generate_cmd = [
                RUSTSMITH_PATH,
                "-t",
                ground.threads,
                "-n",
                ground.rustsmiths_per_cycle,
                "--directory",
                rustsmith_cases_folder,
            ]
            try:
                subprocess.run(rustsmith_generate_cmd, timeout=timer.remaining)
            except subprocess.TimeoutExpired as e:
                print(
                    f"Time quota ran out: stopping generation early after {e.timeout}s."
                )

            # attempt kill using generated test cases
            kill_results = try_killing_with(rustsmith_cases_folder, mutant, ground)

            # update overall killing record, keep test cases if new coverage found
            for rustsmith_file, detection in kill_results.items():
                if detection in coverage:
                    continue

                # we have a killer with new coverage of the mutant: move to mutant's killers folder
                saved_rustsmith_file = rustsmith_file.rename(
                    ground.out_dir / str(mutant) / f"{detection.name}_{random_str()}"
                )

                # update killings record
                coverage[detection] = saved_rustsmith_file

            # clean up generated test cases
            for file in rustsmith_cases_folder.rglob("*"):
                file.unlink()

            # see if coverage now sufficient
            if sufficient_for_level(ground.level, set(coverage.keys())):
                return


def main():
    args = parse_args()

    # prepare the killing ground
    kill_setting = KillingGroundSettings(
        args.minutes_per_mutant,
        args.level,
        args.use_spare_quota,
        args.cases_per_cycle,
        args.rustsmith_path,
        args.out_dir,
        args.threads,
    )
    print(kill_setting)

    # prepare directories structure
    _prepare_killing_ground(args.mutants, args.out_dir)

    # try to kill each mutant
    for mutant in args.mutants:
        attempt_murder(mutant, kill_setting)


if __name__ == "__main__":
    main()
