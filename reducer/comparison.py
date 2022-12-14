import string
import random
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import shutil

@dataclass
class BugConfig:
    version: str
    opt_flag: str
    mutation: int = 0
    compiler_path: str = "rustc"

@dataclass
class Bug:
    v1_config: BugConfig
    v2_config: BugConfig
    path: Path
    cli_args_path: Optional[Path] = None # default: no args
    time_limit: float = 0.10

def _random_str(size : int = 16, chars : str = string.ascii_letters+string.digits) -> str:
    """
    Gets one of the (26 * 2 + 10)^16 ~ O(10^28) possible strings
    """
    return ''.join(random.choice(chars) for _ in range(size))

def _create_reduce_folder(bug: Bug, folder_root: Path, retries : int = 3) -> Path:
    """
    Creates the reduce folder for the test case in `test_case_path`
    """
    # bug_name = [filename].rs
    bug_name = bug.path.name
    # folder_name = [filename]_hash_str
    folder_name = f"{bug_name.rsplit('.', maxsplit=1)[0]}_{_random_str()}"

    # make root folder
    reduce_folder = folder_root / folder_name
    try: 
        print(reduce_folder)
        reduce_folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError as e:
        print("folder name collision:", reduce_folder)
        if retries > 0: 
            _create_reduce_folder(bug, folder_root, retries - 1) # try again

    return reduce_folder

def prepare_reduce_folder(
    bug: Bug, 
    folder_root: Path,
    creduce_script_template_path : Path
) -> Path:
    """
    Creates a folder in `folder_root` for `bug`. 
    The folder will have name `<bug.path.name>_<salt>`.
    A tempalate `creduce_script_template_path` will be used to generate the 'interestingness' test script.
    Created structure:

    folder_root/
        interesting.sh  # the interestingness test
        bug.rs          # the bug
        bug-info.txt    # bug information
    """

    # create and populate folder with bug 
    reduce_folder = _create_reduce_folder(bug, folder_root)
    bug_path = (reduce_folder / "bug.rs")
    shutil.copy(bug.path, bug_path)
    
    # bug information (for tracing back on the bug)
    with open(reduce_folder/"bug-info.txt", "w") as f:
        f.write(str(bug))

    # create creduce interestingness script
    arguments = ""
    if bug.cli_args_path:
        arguments = bug.cli_args_path.open().read().strip()

    script = ""
    with creduce_script_template_path.open() as f:
        script = f.read().format(
            arguments    = arguments,
            rustc_v1     = bug.v1_config.version,
            opt_1        = bug.v1_config.opt_flag,
            mutation_1   = bug.v1_config.mutation,
            rustc_v2     = bug.v2_config.version,
            opt_2        = bug.v2_config.opt_flag,
            mutation_2   = bug.v2_config.mutation,
            time_limit   = bug.time_limit,
            rustc_binary = bug.v1_config.compiler_path,
            file         = bug.path.name
        )
        assert bug.v1_config.compiler_path == bug.v2_config.compiler_path
    
    # write script to bug folder
    script_path = reduce_folder / "interesting.sh"
    script_path.touch()
    script_path.write_text(script)
    script_path.chmod(script_path.stat().st_mode | 0o111) # chmod +x

    return reduce_folder

if __name__ == '__main__':
    rustc_binary = "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"
    bug2 = Bug(
        v1_config=BugConfig("", "0", 0,  rustc_binary),
        v2_config=BugConfig("", "0", 55, rustc_binary),
        path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.rs',
        cli_args_path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.txt'
    )
    prepare_reduce_folder(bug2, Path('.')/"reduce", Path('.')/"shell-script-templates"/"triggers_bug.sh")