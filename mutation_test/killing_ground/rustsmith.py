import argparse
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
import subprocess
from multiprocessing import Pool
import shutil

from utils import timeout, random_str
from mutation_test.mutation_coverage import MutationContext, check_all
from mutation_test.settings import Detection, MUTATED_RUSTC_PATH, TEMPLATE_SCRIPT_PATH

RUSTSMITH_ROOT = Path("/home/jacob/Projects/rustsmith")
RUSTSMITH_PATH = RUSTSMITH_ROOT / "rustsmith/bin/rustsmith"
DEFAULT_OUT_DIR = (
    RUSTSMITH_ROOT / "rustsmith-validator-reduce/mutation_test/killing_ground/out"
)

_RUSTSMITH_FOLDER_NAME = "_rustsmith"
_REDUCTION_FOLDER_NAME = "_reduce"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m mutation_test.round_robin.rustsmith",
        description="Use RustSmith to massacre mutants.",
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
    envs = []
    for case in cases_root.rglob("*.rs"):
        envs.append(
            MutationContext(
                MUTATED_RUSTC_PATH, mutant, 
                case, case.with_suffix(".txt"),
                reduce_root=ground.out_dir / _REDUCTION_FOLDER_NAME, 
                template_script_path=TEMPLATE_SCRIPT_PATH,
                keep_folder=False, 
                panic_kill_is_interesting=False,
                bin_diff_is_interesting=False,
                output_error_is_interesting=False
            )
        )
    results = check_all(envs)

    unwanted_results = set([Detection.UNDETECTED, Detection.COMPILE_TIMEOUT_STOPPED_EARLY])
    return {context: detection for context, detection in results.items()
            if detection not in unwanted_results}


def attempt_murder(mutant: int, ground: KillingGroundSettings) -> None:
    """
    Attempt to kill `mutant` within time limit `timeout`.
    """
    coverage: dict[Detection, Path] = {}

    with timeout(ground.minutes_per_mutant * 60) as timer:
        while True:
            if timer.timed_out:
                print(f"Out of time for {mutant}. Maybe another day...\n")
                return
            print(f"Attempting to kill mutant {mutant}, {timer.remaining}s left.")

            # generate test cases
            rustsmith_cases_folder = ground.out_dir / _RUSTSMITH_FOLDER_NAME
            rustsmith_generate_cmd = [
                str(RUSTSMITH_PATH),
                "-t",
                str(ground.threads),
                "-n",
                str(ground.rustsmiths_per_cycle),
                "--directory",
                str(rustsmith_cases_folder),
            ]
            print("Generating Rust files:", " ".join(rustsmith_generate_cmd))
            try:
                subprocess.run(rustsmith_generate_cmd, timeout=timer.remaining)
            except subprocess.TimeoutExpired as e:
                print(
                    f"Time quota ran out: stopping generation early after trying for {e.timeout}s."
                )

            # attempt kill using generated test cases
            kill_results = try_killing_with(rustsmith_cases_folder, mutant, ground)
            print(f"Test results of m{mutant}: {kill_results}")

            # update overall killing record, keep test cases if new coverage found
            for rustsmith_file, detection in kill_results.items():
                if detection in coverage:
                    continue
                print(f"Found new coverage for {mutant}: {detection.name}")
                # we have a killer with new coverage of the mutant: move to mutant's killers folder
                saved_rustsmith_file = rustsmith_file.rename(
                    ground.out_dir / str(mutant) / f"{detection.name}_{random_str()}"
                )

                # update killings record
                coverage[detection] = saved_rustsmith_file

            # clean up generated test cases
            for file in rustsmith_cases_folder.glob("*"):
                shutil.rmtree(file)

            # see if coverage now sufficient
            if sufficient_for_level(ground.level, set(coverage.keys())):
                print(f"Mutant {mutant} sufficiently killed! Moving on...\n")
                return

            print(f"Mutant {mutant} stubbornly survived. Trying new batch of test cases.")


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
