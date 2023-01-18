"""
script to find the mutation coverage of all Rust scripts in a folder.
caches the result in a shelve file.
"""
from mutation_test.mutation_coverage import (
    check_all, get_default_args_path,
    MutationContext, 
)
from mutation_test.settings import (
    MUTATED_RUSTC_PATH, DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, MAX_MUTANT, RUST_BUILD_ROOT
)

from pathlib import Path
import shelve

CLEAR_LINE_CHAR = "\033[2K"

def compute_rustsmith_mut_coverage(results: shelve.Shelf, root: Path) -> None:
    for i, file in enumerate(root.rglob("*.rs")):
        # dont redo what we've already calculated
        if (i+1) < 0:
            continue

        print(f"{CLEAR_LINE_CHAR}Computing coverage for file #{i+1}: {file}", end="\r")
        envs = [MutationContext(MUTATED_RUSTC_PATH, mutant, 
                                file, get_default_args_path(file), 
                                DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, False,
                                False, False, False)
                for mutant in range(1, MAX_MUTANT)]
        results[file.as_posix()] = check_all(envs, jobs=8)

def compute_rustc_mut_coverage(results: shelve.Shelf, root: Path) -> None:
    for i, file in enumerate(root.rglob("*.rs")):
        if (i+1) < 0: 
            continue

        print(f"{CLEAR_LINE_CHAR}Computing coverage for file #{i+1}: {file}", end="\r")
        envs = [MutationContext(MUTATED_RUSTC_PATH, mutant,
                                file, None, 
                                DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, False,
                                False, False, False)
                for mutant in range(1, MAX_MUTANT)]
        results[file.as_posix()] = check_all(envs, jobs=8)

def main() -> None: 
    """
    - Walks over all .rs files in the `tests` folder
    - Compute their mutation coverage
    - Stores them in file
    """
    # RustSmith evaluations
    with shelve.open("mutation_test/rustsmith_cov_results/store") as results:
        compute_rustsmith_mut_coverage(results, Path("mutation_test/test_cases_filtered"))

    # Rustc evaluations
    # with shelve.open("mutation_test/rustc_cov_results/store") as results:
    #     compute_rustc_mut_coverage(results, RUST_BUILD_ROOT / "src/test/mir-opt")

if __name__ == "__main__":
    main()