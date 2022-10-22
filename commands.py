import os
import platform
import subprocess
import sys
from pathlib import Path


def bootstrap():
    """
    Called when first non-standard lib import fails.

    We need at least pip-tools, typer and rich to use this script.
    """

    def get_base_prefix_compat():
        """Get base/real prefix, or sys.prefix if there is none."""
        return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

    def in_virtualenv():
        return get_base_prefix_compat() != sys.prefix

    if not in_virtualenv():
        print("Please create a virtual environment first and activate it!")
        sys.exit(1)
    print("Empty virtualenv, installing development requirements..")
    subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements/develop.txt"])


try:
    import typer
except ImportError:
    bootstrap()
    import typer

from rich import print  # noqa

cli = typer.Typer()


def get_pythonpath():
    """Add project root and model directory to string"""
    project_root = str(Path(__file__).parent.resolve())
    model_root = str(Path(__file__).parent / "model")
    return f"{project_root}:{model_root}"


def env_with_pythonpath():
    """Get en environment dict with includes PYTHONPATH"""
    env = os.environ.copy()
    env["PYTHONPATH"] = get_pythonpath()
    return env


@cli.command()
def mypy():
    """Run Mypy (configured in pyproject.toml)"""
    subprocess.call(["mypy", "."])


@cli.command()
def test():
    subprocess.call(["python", "-m", "pytest"], env=env_with_pythonpath())


@cli.command()
def coverage():
    """
    Run and show coverage.
    """
    subprocess.call(["coverage", "run", "-m", "pytest"], env=env_with_pythonpath())
    subprocess.call(["coverage", "html"])
    if platform.system() == "Darwin":
        subprocess.call(["open", "htmlcov/index.html"])
    elif platform.system() == "Linux" and "Microsoft" in platform.release():  # on WSL
        subprocess.call(["explorer.exe", r"htmlcov\index.html"])


@cli.command()
def update():
    """
    Update the development environment by calling:
    - pip-compile production.in develop.in -> develop.txt
    - pip-compile production.in -> production.txt
    - pip-sync develop.txt
    """
    base_command = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--upgrade",
        "--allow-unsafe",
        "--generate-hashes",
        "requirements/production.in",
    ]
    subprocess.call(  # develop + production
        [
            *base_command,
            "requirements/develop.in",
            "--output-file",
            "requirements/develop.txt",
        ]
    )
    subprocess.call(  # production only
        [
            *base_command,
            "--output-file",
            "requirements/production.txt",
        ]
    )
    subprocess.call([sys.executable, "-m", "piptools", "sync", "requirements/develop.txt"])


if __name__ == "__main__":
    cli()
