"""
script to find the mutation coverage of all Rust scripts in a folder.
caches the result in a shelve file.
"""
from mutation_test.mutation_coverage import (
    check_all, get_default_args_path,
    TestContext, 
    MUTATED_RUSTC_PATH, DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, MAX_MUTANT
)

from pathlib import Path
import shelve

CLEAR_LINE_CHAR = "\033[2K"

def compute_mutation_coverage(results: shelve.Shelf, root: Path) -> None:
    for i, file in enumerate(root.rglob("*.rs")):
        # dont redo what we've already calculated
        if (i+1) < 32:
            continue

        print(f"{CLEAR_LINE_CHAR}Computing coverage for file #{i+1}: {file}", end="\r")
        env = TestContext(MUTATED_RUSTC_PATH, file, get_default_args_path(file), 
                          False, False, False, 
                          DEFAULT_REDUCE_ROOT, TEMPLATE_SCRIPT_PATH, False)
        results[file.as_posix()] = check_all(env, 1, MAX_MUTANT, jobs=12)

def main() -> None: 
    """
    - Walks over all .rs files in the `tests` folder
    - Compute their mutation coverage
    - Stores them in file
    """
    with shelve.open("mutation_test/mutation_cov_results/store") as results:
        compute_mutation_coverage(results, Path("mutation_test/tests"))

if __name__ == "__main__":
    main()