"""
For a bug, we will reduce it by:
- Copy the found bug into its own folder
- Generate the shell script to reproduce the bug. TestCases are based on different results when compiling the same file under different settings:
    - Different compiler versions
    - Different optimisation flags
- Call CReduce on the file with the generated bug-detection script
"""
from reducer.comparison import TestCase, CompilerConfig, ReductionEnv, prepare_reduce_folder

import subprocess
from pathlib import Path

def reduce(
    case: TestCase, 
    env: ReductionEnv
) -> Path:
    reduce_folder = prepare_reduce_folder(case, env)

    # call creduce
    creduce_command = f"creduce ./interesting.sh test-case.rs --not-c"
    subprocess.run(creduce_command.split(), cwd=reduce_folder)

    return reduce_folder / case.path.name

def main() -> None:
    env = ReductionEnv()
    case1 = TestCase(
        v1_config=CompilerConfig("1.45.0", "0"),
        v2_config=CompilerConfig("1.45.0", "2"),
        path=Path('./reducer/original_bugs/bug1-in-1.40/bug1-in-1.40.rs')
    )

    case2 = TestCase(
        v1_config=CompilerConfig("1.61.0", "0"),
        v2_config=CompilerConfig("1.61.0", "s"),
        path=Path('./reducer/original_bugs/bug3-in-1.61.0/bug3-in-1.61.0.rs'),
        cli_args_path=Path('./reducer/original_bugs/bug3-in-1.61.0/args.txt')
    )
    reduce(case2, env) 

if __name__ == '__main__':
    main()