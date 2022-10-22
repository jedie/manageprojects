import platform
import subprocess
import sys
from pathlib import Path

import typer
from rich import print  # noqa

cli = typer.Typer()


def verbose_call(*popen_args, **kwargs):
    popen_args = [str(arg) for arg in popen_args]  # e.g.: Path() -> str
    print(f'\n+ {" ".join(popen_args)}\n')
    return subprocess.call(popen_args, **kwargs)


def which(file_name: str) -> Path:
    venv_bin_path = Path(sys.executable).parent
    assert venv_bin_path.is_dir()
    bin_path = venv_bin_path / file_name
    if not bin_path.is_file():
        raise FileNotFoundError(f'File {file_name}!r not found in {venv_bin_path}')
    return bin_path


@cli.command()
def mypy():
    """Run Mypy (configured in pyproject.toml)"""
    verbose_call(which("mypy"), ".")


@cli.command()
def test():
    verbose_call(sys.executable, "-m", "pytest")


@cli.command()
def coverage():
    """
    Run and show coverage.
    """
    coverage_bin = which('coverage')
    verbose_call(coverage_bin, "run", "-m", "pytest")
    verbose_call(coverage_bin, "html")
    if platform.system() == "Darwin":
        verbose_call("open", "htmlcov/index.html")
    elif platform.system() == "Linux" and "Microsoft" in platform.release():  # on WSL
        verbose_call("explorer.exe", r"htmlcov\index.html")


@cli.command()
def update():
    """
    Update the development environment by calling:
    - pip-compile production.in develop.in -> develop.txt
    - pip-compile production.in -> production.txt
    - pip-sync develop.txt
    """
    base_command = [
        which("pip-compile"),
        "--upgrade",
        "--allow-unsafe",
        "--generate-hashes",
        "requirements/production.in",
    ]
    verbose_call(  # develop + production
        *base_command,
        "requirements/develop.in",
        "--output-file",
        "requirements/develop.txt",
    )
    verbose_call(  # production only
        *base_command,
        "--output-file",
        "requirements/production.txt",
    )
    verbose_call(which("pip-sync"), "requirements/develop.txt")


@cli.command()
def version():
    """Print version and exit"""
    print('manageprojects v', end="")
    from manageprojects import __version__

    print(__version__)
