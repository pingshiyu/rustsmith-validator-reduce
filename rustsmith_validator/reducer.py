"""
For a bug, we will reduce it by:
- Copy the found bug into its own folder
- Generate the shell script to reproduce the bug. Bugs are based on different results when compiling the same file under different settings:
    - Different compiler versions
    - Different optimisation flags
- Call CReduce on the file with the generated bug-detection script
"""
import string
import random
import subprocess
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import shutil

@dataclass
class BugConfig:
    version: str
    opt_flag: str

@dataclass
class Bug:
    v1_config: BugConfig
    v2_config: BugConfig
    path: Path
    cli_args_path: Optional[Path] = None # default: no args

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

def reduce(
    bug: Bug, 
    folder_root: Path = Path("."), 
    creduce_script_template_path : Path = Path("./shell-script-templates")/"triggers_bug.sh",
    time_limit_per_run: float = 0.50
) -> None:
    # create and populate folder with bug 
    reduce_folder = _create_reduce_folder(bug, folder_root)
    shutil.copy(bug.path, reduce_folder / "bug.rs")

    # create creduce interestingness script
    arguments = ""
    if bug.cli_args_path:
        arguments = bug.cli_args_path.open().read().strip()

    script = ""
    with creduce_script_template_path.open() as f:
        script = f.read().format(
            arguments=arguments,
            rustc_v1=bug.v1_config.version,
            opt_1=bug.v1_config.opt_flag,
            rustc_v2=bug.v2_config.version,
            opt_2=bug.v2_config.opt_flag,
            time_limit=time_limit_per_run
        )
    
    # write script to bug folder
    script_path = reduce_folder / "triggers_bug.sh"
    script_path.touch()
    script_path.write_text(script)
    script_path.chmod(script_path.stat().st_mode | 0o111) # chmod +x

    # call creduce
    creduce_command = "creduce ./triggers_bug.sh bug.rs --not-c"
    subprocess.run(creduce_command.split(), cwd=reduce_folder)

def main() -> None:
    bug1 = Bug(
        v1_config=BugConfig("1.45.0", "0"),
        v2_config=BugConfig("1.45.0", "2"),
        path=Path('.')/"original_bugs"/"bug1-in-1.40"/"bug1-in-1.40.rs"
    )

    bug2 = Bug(
        v1_config=BugConfig("1.61.0", "0"),
        v2_config=BugConfig("1.61.0", "s"),
        path=Path('.')/"original_bugs"/"bug3-in-1.61.0"/"bug3-in-1.61.0.rs",
        cli_args_path=Path('.')/"original_bugs"/"bug3-in-1.61.0"/"args.txt"
    )
    reduce(bug2, Path('.')/"reduce") 

if __name__ == '__main__':
    main()