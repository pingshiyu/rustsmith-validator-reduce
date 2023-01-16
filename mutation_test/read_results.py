import shelve
from pathlib import Path
import pprint as pp
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

# from mutation_test.mutation_coverage import Detection
from enum import Enum, auto
class Detection(Enum):
    UNKNOWN = 0
    DETECTED = auto()
    UNDETECTED = auto() # bug not present
    PANIC = auto()
    COMPILE_TIMEOUT = auto()
    BINARY_ERRORS = auto()
    BINARY_TIMEOUT = auto()

def read_results(store_path: Path) -> Dict:
    """
    Reads a coverage Dict of the type:
        string -> [Any]
    """
    coverage = {}
    with shelve.open(str(store_path)) as results:
        errors = 0
        for i, k in enumerate(results.keys()):
            try:
                coverage[k] = results[k]
                # print(f"#{i+1}: {k} ->", results[k])
            except EOFError:
                errors += 1
        
        print("Errors:", errors)
    return coverage

def transpose_coverage_results(coverage: Dict) -> Dict:
    """
    Converts a coverage record of mapping:
        filename -> [(mutation, Detection)]
    Into a mapping:
        mutation -> [(filename, Detection)]
    """
    coverage_t = {}
    for file, kills in coverage.items():
        if not kills or kills[-1][0] == -1: # no kills or aborted due to too many timeouts
            continue
        for mutant, kill_method in kills:
            coverage_t[mutant] = coverage_t.get(mutant, []) + [(file, kill_method)]
    return coverage_t

def summarize_dict(data: dict):
    """
    Similar to the version below but just minor modifications to get rid of warnings
    """
    all_integers = []
    all_enums = []
    detected_tuples = []
    skipped_files = []

    for file, numbers in data.items():
        if not numbers or numbers[-1][0] == -1:
            skipped_files.append(file)
            continue
        integers = [x[0] for x in numbers]
        enums = [x[1] for x in numbers]
        all_integers.extend(integers)
        all_enums.extend(enums)

        for number in numbers:
            if number[1] == Detection.DETECTED:
                detected_tuples.append((number[0], file))
    detected_tuples_df = pd.DataFrame(detected_tuples, columns=("Mutation", "Filename") )

    # Create frequency table for integers
    integer_counter = Counter(all_integers)
    integer_df_data = [] # pd.DataFrame(columns=["Mutation", "Count"])
    for integer, count in integer_counter.items():
        integer_df_data.append([integer, count])
    integer_df_sorted = pd.DataFrame(integer_df_data, columns=["Mutation", "Count"]).sort_values("Count")

    # Create frequency table for enums
    enum_counter = Counter(all_enums)
    enum_df_data = [] # pd.DataFrame(columns=["Enum", "Count"])
    for enum, count in enum_counter.items():
        enum_df_data.append([enum, count])
    enum_df = pd.DataFrame(enum_df_data, columns=["Enum", "Count"])

    return integer_df_sorted, enum_df, detected_tuples_df, skipped_files

def summarize_dict_chatgpt(data: dict):
    """
    This function is almost writen entirely by ChatGPT (!!!)
    I just told it my requirements, and it wrote this prorgam.
    """
    summary = {}
    all_integers = []
    all_enums = []
    detected_tuples = []
    skipped_files = []

    for file, numbers in data.items():
        if not numbers or numbers[-1][0] == -1:
            skipped_files.append(file)
            continue
        integers = [x[0] for x in numbers]
        enums = [x[1] for x in numbers]
        all_integers.extend(integers)
        all_enums.extend(enums)

        for number in numbers:
            if number[1] == Detection.DETECTED:
                detected_tuples.append((number[0], file))
    detected_tuples_df = pd.DataFrame(detected_tuples, columns=("Mutation", "Filename") )

    # Create frequency table for integers
    integer_counter = Counter(all_integers)
    integer_df = pd.DataFrame(columns=["Mutation", "Count"])
    for integer, count in integer_counter.items():
        integer_df = integer_df.append({"Mutation": integer, "Count": count}, ignore_index=True)
    integer_df_sorted = integer_df.sort_values("Count")

    # Create frequency table for enums
    enum_counter = Counter(all_enums)
    enum_df = pd.DataFrame(columns=["Enum", "Count"])
    for enum, count in enum_counter.items():
        enum_df = enum_df.append({"Enum": enum, "Count": count}, ignore_index=True)

    return integer_df_sorted, enum_df, detected_tuples_df, skipped_files

def main() -> None:
    coverage = read_results(Path("mutation_test/mutation_cov_results/store"))
    
    # table of mutation coverage of RustSmith files
    mut_cov_table, enum_freq_table, detected, skipped = summarize_dict(coverage)
    print(mut_cov_table)

    # RustSmith distribution of coverage results, e.g. timeout, abandoned, panic, errors etc
    print(enum_freq_table)

    # table of Detection.DETECTED results
    print(detected)

    # number of files skipped
    print(f"skipped files: {len(skipped)} / {len(coverage.keys())}")

if __name__ == '__main__':
    main()