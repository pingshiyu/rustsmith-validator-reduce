"""
For a bug, we will reduce it by:
- Copy the found bug into its own folder
- Generate the shell script to reproduce the bug. Bugs are based on different results when compiling the same file under different settings:
    - Different compiler versions
    - Different optimisation flags
- Call CReduce on the file with the generated bug-detection script
"""
from comparison import Bug, BugConfig, prepare_reduce_folder

import subprocess
from pathlib import Path

def reduce(
    bug: Bug, 
    folder_root: Path = Path("."), 
    creduce_script_template_path : Path = Path("./shell-script-templates")/"triggers_bug.sh"
) -> Path:
    reduce_folder = prepare_reduce_folder(
            bug, folder_root=folder_root, creduce_script_template_path=creduce_script_template_path)

    # call creduce
    creduce_command = f"creduce ./interesting.sh bug.rs --not-c"
    subprocess.run(creduce_command.split(), cwd=reduce_folder)

    return reduce_folder / bug.path.name

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