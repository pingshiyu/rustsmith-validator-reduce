import argparse
import concurrent.futures
import os
import shutil
import subprocess
import time
from pathlib import Path
from enum import Enum

import typer
from click._termui_impl import ProgressBar, V

class Status(Enum):
    NULL = 0
    SUCCESS = 1
    FAILURE = 2

def compile(binary_file_path: str, file_path: Path, flag: str) -> Status: 
    shutil.rmtree(binary_file_path, ignore_errors=True)
    os.mkdir(binary_file_path)
    fmt_command = f"rustfmt {file_path}"
    subprocess.run(fmt_command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    command = f"rustc -C opt-level={flag} {file_path} -o {binary_file_path / 'out'}"
    result = subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with open(binary_file_path / "compile.log", "w") as file:
        file.write(result.stderr.decode())

    if result.returncode == 0:
        return Status.SUCCESS
    return Status.FAILURE

def run(file_path: Path, binary_file_path: str, directory: str, timeout: float):
    try:
        start_time = time.time()
        with open(file_path.parent / (file_path.stem + '.txt')) as file:
            cli_args = file.read()
        run_result = subprocess.run(
            [f"{binary_file_path / 'out'}", *cli_args.split(" ")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        end_time = time.time() - start_time
        with open(Path(directory) / "time.log", "a") as file:
            file.write(f"{end_time}\n")
        with open(binary_file_path / "output.log", "w") as file:
            file.write(run_result.stdout.decode())
            file.write(run_result.stderr.decode())
            file.write(f"Exit Code {run_result.returncode}")
    except subprocess.TimeoutExpired:
        with open(binary_file_path / "output.log", "w") as file:
            file.write("Timeout")

def compile_and_run(file_path: Path, flag: str, progress: ProgressBar[V], directory: str, timeout: float) -> None:
    binary_file_path = file_path.parent / f"O{flag}"
    if compile(binary_file_path, file_path, flag) == Status.SUCCESS:
       run(binary_file_path, file_path, directory, timeout)
    progress.update(1)

def main(threads: int = 15, timeout: float = 5.0) -> None:
    directory = "outRust"
    files = [dI for dI in os.listdir(directory) if os.path.isdir(os.path.join(directory, dI))]
    files.sort(key=lambda x: int(x.split("file")[1]))
    optimization_flags = ["0", "1", "2", "3", "s", "z"]
    with typer.progressbar(label="Progress", length=len(files) * len(optimization_flags)) as progress:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            tasks = []
            for file in files:
                for flag in optimization_flags:
                    tasks.append(
                        executor.submit(
                            compile_and_run, Path(directory, file, file + ".rs"), flag, progress, directory, timeout
                        )
                    )
            for future in concurrent.futures.as_completed(tasks):
                future.result()
    for file in files:
        outputs = []
        for flag in optimization_flags:
            path = Path(directory, file, f"O{flag}", "output.log")
            if path.exists():
                with open(path, "r") as output_file:
                    outputs.append(output_file.read())
            else:
                print(f"{file}: Compilation Failure")
                break
        if len(outputs):
            print(f"{file}: {'All correct' if all(x == outputs[0] for x in outputs) else 'Bug found'}")


if __name__ == "__main__":
    typer.run(main)
