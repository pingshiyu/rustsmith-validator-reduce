from mutation_test.rustc_cov.mutation_coverage import mutant_kill_strength, MutationResult
import glob
import shelve
from dataclasses import asdict
import pprint as pp

def _update_storage(storage: shelve.Shelf, mutant_key: str, file: str, result: MutationResult) -> None:
    new_entry = asdict(result)
    new_entry.update({"file": file})

    record = storage.get(mutant_key, [])
    record.append(new_entry)
    storage[mutant_key] = record

    pp.pprint((mutant_key, new_entry))

def evaluate_test_cases(folder_root: str, rustc_m_location: str, storage: shelve.Shelf):
    rs_files = [fp for fp in glob.glob(f"{folder_root}/**/*.rs")]

    print(len(rs_files))
    for mutation_no in range(272, 381):
        mutation_key = str(mutation_no)
        storage[mutation_key] = []
        
        print(f"Testing mutation number {mutation_key}")
        try:
            for file in rs_files:
                print(f"Testing file: {file}")
                result = mutant_kill_strength(
                    mutation_no,
                    rustc_m_location,
                    file)

                _update_storage(storage, mutation_key, file, result)
        except Exception as e:
            print(e)
            continue

        print("INCREMENTING MUTATION NUMBER")


if __name__ == "__main__":
    with shelve.open("mutation_test/rustc_cov/results/store") as store: 
        evaluate_test_cases(
            "/home/jacob/projects/rustsmith/rust-mutcov/src/test/mir-opt",
            "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc",
            store)