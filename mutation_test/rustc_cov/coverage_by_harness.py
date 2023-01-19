"""
Evaluate the mutation coverage of the Rustc test suite, by invoking the test harness.
"""
import subprocess
from pathlib import Path
from enum import Enum, auto
import os
import shelve
import re
from typing import Any

from mutation_test.settings import MAX_MUTANT
from utils import SECONDS_IN_MINUTE

RUSTC_BUILD_ROOT = Path("/home/jacob/projects/rustsmith/rust-mutcov")

class RustcMutantDetection(Enum):
    UNDETECTED = auto()
    DETECTED = auto()

class BadOutputException(Exception):
    pass

def _summarise_output(xpy_stdout: str) -> dict[str, Any]:
    results_re = re.compile((r"test result: (?P<STATUS>\w+)\. "
                             r"(?P<PASSED>\d+) passed; "
                             r"(?P<FAILED>\d+) failed; "
                             r"(?P<IGNORED>\d+) ignored; "
                             r"(?P<MEASURED>\d+) measured; "
                             r"(?P<FILTERED>\d+) filtered out; "
                             r"finished in (?P<TIME_TAKEN>[^s]+)s"))
    match = re.search(results_re, xpy_stdout)
    if not match:
        raise BadOutputException(f"No summary line on string: \n{xpy_stdout}")
    summary = match.groupdict()

    int_keys = ['PASSED', 'FAILED', 'IGNORED', 'MEASURED', 'FILTERED']
    for key in int_keys:
        summary[key] = int(summary[key])
    summary['TIME_TAKEN'] = float(summary['TIME_TAKEN'])

    return summary

def _empty_summary() -> dict[str, Any]:
    # for timeouts
    return {
        'STATUS': 'TIMEOUT',
        'PASSED': 0,
        'FAILED': 0,
        'IGNORED': 0,
        'MEASURED': 0,
        'FILTERED': 0,
        'TIME_TAKEN': float('inf'),
    }

def _get_save_entry(summary: dict[str, Any], stdout: str, stderr: str) -> dict[str, Any]:
    return {
        "stdout": stdout,
        "stderr": stderr,
        "summary": summary
    }

def main():
    mutation_env = os.environ.copy()

    # run through all mutations
    with shelve.open("mutation_test/rustc_cov_results_harness/store") as results:
        for m in range(0, MAX_MUTANT+1):
            mutation_env["RUSTC_MUTATION_NUMBER"] = f"{m}"
            test_command = ["./x.py", "test", "test/mir-opt", "--force-rerun"]

            print(f"Testing mutant {m}")
            try:
                mut_compile_result = subprocess.run(
                    test_command,
                    timeout=5 * SECONDS_IN_MINUTE,
                    env=mutation_env,
                    cwd=RUSTC_BUILD_ROOT, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.TimeoutExpired as e:
                # write timeout into summary
                print(f"Mutant {m} evaluation timed out!\n")
                results[f"{m}"] = _get_save_entry(_empty_summary(), "", "")
                continue

            stdout = mut_compile_result.stdout.decode("utf-8")
            stderr = mut_compile_result.stderr.decode("utf-8")
            summary = _summarise_output(stdout)
            results[f"{m}"] = _get_save_entry(summary, stdout, stderr)

            print(f"Results for mutant {m} saved\n")

if __name__ == '__main__':
    main()