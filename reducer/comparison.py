from dataclasses import dataclass
from typing import Optional, Dict
from pathlib import Path
import shutil
import pprint as pp

from utils import random_str
from mutation_test.settings import COMPILE_TIMEOUT, OUTPUT_TIMEOUT

@dataclass
class CompilerConfig:
    version: str
    flags: str
    mutation: int = 0
    compiler_path: str = "rustc"

@dataclass
class TestCase:
    v1_config: CompilerConfig
    v2_config: CompilerConfig
    path: Path
    cli_args_path: Optional[Path] = None # default: no args
    time_limit_compile: float = COMPILE_TIMEOUT
    time_limit_bin: float = OUTPUT_TIMEOUT

@dataclass
class ReductionEnv:
    # return values from bug kills
    kill_return_values: Dict[str, int]
    # where to put the reduction folders
    reduction_root: Path = Path("reducer/reduce")
    # template to generate interesting.sh script
    creduce_script_template_path: Path = Path("reducer/shell-script-templates/mutation_detection.sh")

def _create_reduce_folder(test_case: TestCase, folder_root: Path, retries : int = 3, verbose: bool = False) -> Path:
    """
    Creates the reduce folder for the test case in `test_case_path`
    """
    # test_case_name = [filename].rs
    test_case_name = test_case.path.name
    # folder_name = [filename]_hash_str
    folder_name = f"{test_case_name.rsplit('.', maxsplit=1)[0]}_{random_str()}"

    # make root folder
    reduce_folder = folder_root / folder_name
    try: 
        if verbose: print("folder created:", reduce_folder)
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
            arguments           = arguments,
            rustc_v1            = test_case.v1_config.version,
            flags_1             = test_case.v1_config.flags,
            mutation_1          = test_case.v1_config.mutation,
            rustc_v2            = test_case.v2_config.version,
            flags_2             = test_case.v2_config.flags,
            mutation_2          = test_case.v2_config.mutation,
            time_limit_compile  = test_case.time_limit_compile,
            time_limit_bin      = test_case.time_limit_bin,
            rustc_binary        = test_case.v1_config.compiler_path,
            rs_filename         = test_case_path.name,
            **environment.kill_return_values
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

    # test_case2 = TestCase(
    #     v1_config=CompilerConfig("", "0", 0,  rustc_binary),
    #     v2_config=CompilerConfig("", "0", 55, rustc_binary),
    #     path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.rs',
    #     cli_args_path=Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation-test/tests/outRust-379/outRust/file0/')/'file0.txt'
    # )
    # environment = ReductionEnv(Path('.')/"reduce", Path('.')/"shell-script-templates"/"triggers_bug.sh")
    # prepare_reduce_folder(test_case2, environment)

    folder_root = Path('/home/jacob/projects/rustsmith/rustsmith-validator-reduce/mutation_test/tests/outRust-379/outRust/file0')
    test_case_mut = TestCase(
        v1_config=CompilerConfig("", "-Zmir-opt-level=4 -Copt-level=1", 0,  rustc_binary),
        v2_config=CompilerConfig("", "-Zmir-opt-level=4 -Copt-level=1", 10, rustc_binary),
        path=folder_root/'file0.rs',
        cli_args_path=folder_root/'file0.txt'
    )

    from mutation_test.settings import get_kill_return_values

    environment = ReductionEnv(get_kill_return_values(), Path('reducer/reduce'), Path('reducer/shell-script-templates/mutation_detection.sh'))
    produced_folder = prepare_reduce_folder(test_case_mut, environment)
    print("produced:", produced_folder)