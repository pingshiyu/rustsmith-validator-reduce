from enum import Enum, auto
from typing import Dict
from pathlib import Path

RUST_BUILD_ROOT = Path("/home/jacob/Projects/rustsmith/rust-mutcov")
MUTATED_RUSTC_PATH = (RUST_BUILD_ROOT / "build/x86_64-unknown-linux-gnu/stage2/bin/rustc").as_posix()
TEMPLATE_SCRIPT_PATH = Path("reducer/shell-script-templates/mutation_detection.sh")
DEFAULT_REDUCE_ROOT = Path("reducer/reduce/mutations/")
MAX_MUTANT = 380

class Detection(Enum):
    UNKNOWN = auto()
    UNDETECTED = auto() # bug not present
    COMPILE_PANIC = auto()
    COMPILE_TIMEOUT = auto()
    BINARY_DIFFERENCE = auto()
    OUTPUT_ERRORS = auto()
    OUTPUT_TIMEOUT = auto()
    OUTPUT_DIFFERENCE = auto() # aka DETECTED

DETECTION_CODE = {
    Detection.UNDETECTED: 1,
    Detection.COMPILE_PANIC: 2,
    Detection.COMPILE_TIMEOUT: 3,
    Detection.BINARY_DIFFERENCE: 4,
    Detection.OUTPUT_ERRORS: 5,
    Detection.OUTPUT_TIMEOUT: 6,
    Detection.OUTPUT_DIFFERENCE: 0
}

def get_kill_return_values() -> Dict[str, int]:
    return {
        "undetected_return":        DETECTION_CODE[Detection.UNDETECTED],
        "compile_panic_return":     DETECTION_CODE[Detection.COMPILE_PANIC],
        "compile_timeout_return":   DETECTION_CODE[Detection.COMPILE_TIMEOUT],
        "binary_difference_return": DETECTION_CODE[Detection.BINARY_DIFFERENCE],
        "output_timeout_return":    DETECTION_CODE[Detection.OUTPUT_ERRORS],
        "output_err_return":        DETECTION_CODE[Detection.OUTPUT_TIMEOUT],
        "output_diff_return":       DETECTION_CODE[Detection.OUTPUT_DIFFERENCE],
    }

def return_code_to_detection(return_code: int) -> Detection:
    for detection, code in DETECTION_CODE.items():
        if code == return_code:
            return detection
    return Detection.UNKNOWN