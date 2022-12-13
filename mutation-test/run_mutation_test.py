# executes a mutation test on a file.
# that is, compile the file once with mutations, once without
# run the binaries against the same input and report the results

# generate a script to compile the program in two different ways, once with mutations, other without

rustc_path : str = "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"

def _prepare_comparison_script(compiler: str, mutation: int) -> None:
    # arguments assumed to be in same directory as .rs file, but with format .txt
    # e.g. bug.rs has arguments in bug.txt
    pass

def _run_comparison() -> None:
    # executes the generated script, cding and executing the script in the correct location
    pass

def 