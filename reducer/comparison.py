import string
import random
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import shutil
import pprint as pp

@dataclass
class CompilerConfig:
    version: str
    opt_flag: str
    mutation: int = 0
    compiler_path: str = "rustc"

@dataclass
class TestCase:
    v1_config: CompilerConfig
    v2_config: CompilerConfig
    path: Path
    cli_args_path: Optional[Path] = None # default: no args
    time_limit: float = 0.10
    panic_kill_is_bug: bool = False

@dataclass
class ReductionEnv:
    # where to put the reduction folders
    reduction_root: Path = Path("reducer/reduce")
    # template to generate interesting.sh script
    creduce_script_template_path: Path = Path("reducer/shell-script-templates/triggers_bug.sh")

def _random_str(size : int = 16, chars : str = string.ascii_letters+string.digits) -> str:
    """
    Gets one of the (26 * 2 + 10)^16 ~ O(10^28) possible strings
    """
    return ''.join(random.choice(chars) for _ in range(size))

def _create_reduce_folder(test_case: TestCase, folder_root: Path, retries : int = 3) -> Path:
    """
    Creates the reduce folder for the test case in `test_case_path`
    """
    # test_case_name = [filename].rs
    test_case_name = test_case.path.name
    # folder_name = [filename]_hash_str
    folder_name = f"{test_case_name.rsplit('.', maxsplit=1)[0]}_{_random_str()}"

    # make root folder
    reduce_folder = folder_root / folder_name
    try: 
        print("folder created:", reduce_folder)
        reduce_folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("folder name collision:", reduce_folder)
        if retries > 0: 
            _create_reduce_folder(test_case, folder_root, retries - 1) # try again

    return reduce_folder

def prepare_reduce_folder(
    test_case: TestCase, 
    environment: ReductionEnv
) -> Path:
    """
    Creates a folder in `folder_root` for `test_case`. 
    The folder will have name `<test_case.path.name>_<salt>`.
    A tempalate `creduce_script_template_path` will be used to generate the 'interestingness' test script.
    Created structure:

    folder_root/
        interesting.sh        # the interestingness test
        test_case.rs          # the test case
        test-case-info.txt    # test case information
    """
    # create and populate folder with test_case 
    reduce_folder = _create_reduce_folder(test_case, environment.reduction_root)
    test_case_path = (reduce_folder / "test-case.rs")
    shutil.copy(test_case.path, test_case_path)
    
    # test_case information (for tracing back on the test_case)
    with open(reduce_folder/"test-case-info.txt", "w") as f:
        f.write(pp.pformat(test_case))

    # create creduce interestingness script
    arguments = ""
    if test_case.cli_args_path:
        arguments = test_case.cli_args_path.open().read().strip()

    script = ""
    with environment.creduce_script_template_path.open() as f:
        script = f.read().format(
            arguments         = arguments,
            rustc_v1          = test_case.v1_config.version,
            opt_1             = test_case.v1_config.opt_flag,
            mutation_1        = test_case.v1_config.mutation,
            rustc_v2          = test_case.v2_config.version,
            opt_2             = test_case.v2_config.opt_flag,
            mutation_2        = test_case.v2_config.mutation,
            time_limit        = test_case.time_limit,
            rustc_binary      = test_case.v1_config.compiler_path,
            rs_filename       = test_case_path.name,
            panic_kill_return = 0 if test_case.panic_kill_is_bug else 1
        )
        assert test_case.v1_config.compiler_path == test_case.v2_config.compiler_path
    
    # write script to test_case folder
    script_path = reduce_folder / "interesting.sh"
    script_path.touch()
    script_path.write_text(script)
    script_path.chmod(script_path.stat().st_mode | 0o111) # chmod +x

    return reduce_folder

if __name__ == '__main__':
    rustc_binary = "/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"
    test_case2 = TestCase(
        v1_config=CompilerConfig("", "0", 0,  rustc_binary),
        v2_config=CompilerConfig("", "0", 55, rustc_binary),
        path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.rs',
        cli_args_path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.txt'
    )

    environment = ReductionEnv(Path('.')/"reduce", Path('.')/"shell-script-templates"/"triggers_bug.sh")
    prepare_reduce_folder(test_case2, environment)