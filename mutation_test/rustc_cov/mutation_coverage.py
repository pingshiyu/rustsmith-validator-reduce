import os
import subprocess
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass

from mutation_test.mutation_coverage import Detection

# Hierachy of coverage:
# Reached < Binary-Diff < Results-Diff
# Reached < Panic ~ Timeout
# Panic <\= Binary-Diff u Results-Diff (Panic kill means Binary, Results diff not defined)
# Where A < B is defined as:
#   forall (T kills mutant by method B) => (T kills mutant by method A).

# class KillStrength(Enum):
#     # REACHED = auto() # we don't record this
#     SURVIVED = auto()
#     COMPILE_TIMEOUT = auto()
#     COMPILE_PANIC = auto()
#     BINARY_DIFFERENCE = auto()
#     RESULT_DIFFERENCE = auto()

@dataclass
class MutationResult:
    strength: Detection
    original_out: str = ""
    mutant_out: str = ""

class RunResult(Enum):
    OUTPUT = auto()
    TIMEOUT = auto()
    CRASH = auto()


def mutant_kill_strength(mutation_number: int, rustcm_path: str, file_path: str, args_path: Optional[str] = None) -> MutationResult:
    """
    Tests if mutant `mutation_number` is killed by `file_path`.
    Compiles `file_path` with `rustc(mutation_number)` and `rustc`. See how results differ. 
    Outputs how this mutant was killed as a `MutationResult`
    """
    subprocess.run("rm out out-mut".split(" "))

    flags = "-Zmir-opt-level=4 -Copt-level=1"
    compile_command = f"{rustcm_path} {flags} {file_path} -o out"

    ### 1. Compile with rustc(m)
    mutation_env = os.environ.copy()
    mutation_env["RUSTC_MUTATION_NUMBER"] = f"{mutation_number}"
    try:
        mut_compile_result = subprocess.run(
            compile_command.split(" "),
            timeout=10.0,
            env=mutation_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.TimeoutExpired:
        return MutationResult(Detection.COMPILE_TIMEOUT)

    # Copy file from out to out-mut
    subprocess.run("cp out out-mut".split(" "))

    compile_env = os.environ.copy()
    compile_env["RUSTC_MUTATION_NUMBER"] = "-1"
    # compiles to out
    compile_result = subprocess.run(
        compile_command.split(" "), timeout=10.0, env=compile_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # One of the compilers panics. Cannot proceed as we need to compare the produced binaries.
    if mut_compile_result.returncode != compile_result.returncode:
        return MutationResult(Detection.COMPILE_PANIC)
    elif mut_compile_result.returncode != 0 and compile_result.returncode != 0:
        # Both crashed, which is okay, move on
        return MutationResult(Detection.UNDETECTED)

    ### From here on: both compilers produced a binary.
    ### Thus we are in a hierachy: Binary-Diff < Results_Diff
    ### Want to test how strongly we can kill the mutant through `file_path`
    diff_command = "diff out out-mut"
    diff_result = subprocess.run(diff_command.split(" "), timeout=10.0)

    if diff_result.returncode == 0:
        # same compiled binary => cannot possibly kill the mutant
        return MutationResult(Detection.UNDETECTED)

    ### From here on: Binary-Diff is true. Want to check if Results-Diff is true too
    _ = subprocess.run("chmod +x out".split(" "), timeout=10.0)
    _ = subprocess.run("chmod +x out-mut".split(" "), timeout=10.0)

    cli_args = ""
    if args_path:
        with open(args_path) as file:
            cli_args = file.read()

    try:
        out_command = subprocess.run(["./out", *cli_args.split(" ")], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=10.0)
        output_original = str(out_command.stdout) + str(out_command.stderr)
    except subprocess.TimeoutExpired:
        output_original = "Timeout"
    except:
        output_original = "CRASH"

    try:
        out_mut_command = subprocess.run(["./out-mut", *cli_args.split(" ")], stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, timeout=10.0)
        output_mutant = str(out_mut_command.stdout) + str(out_mut_command.stderr)
    except subprocess.TimeoutExpired:
        output_mutant = "Timeout"
    except:
        output_mutant = "CRASH"

    if output_original != output_mutant:
        return MutationResult(Detection.OUTPUT_DIFFERENCE, output_original, output_mutant)
    else:
        # binary was different, but run result was the same!
        return MutationResult(Detection.BINARY_DIFFERENCE)


x = mutant_kill_strength(
    1,
    "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc",
    "/home/jacob/projects/rustsmith/rust-mutcov/src/test/mir-opt/derefer_test_multiple.rs",
)

print(x)
