import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import rich
import typer
from bx_py_utils.path import assert_is_dir, assert_is_file
from darker.__main__ import main as darker_main
from flake8.main.cli import main as flake8_main
from rich import print  # noqa

import manageprojects
from manageprojects.cookiecutter_templates import (
    clone_managed_project,
    start_managed_project,
    update_managed_project,
)
from manageprojects.data_classes import CookiecutterResult
from manageprojects.git import Git
from manageprojects.utilities.log_utils import log_config
from manageprojects.utilities.subprocess_utils import verbose_check_call


logger = logging.getLogger(__name__)


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent
assert_is_dir(PACKAGE_ROOT)
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')


cli = typer.Typer()


def which(file_name: str) -> Path:
    venv_bin_path = Path(sys.executable).parent
    assert venv_bin_path.is_dir()
    bin_path = venv_bin_path / file_name
    if not bin_path.is_file():
        raise FileNotFoundError(f'File {file_name}!r not found in {venv_bin_path}')
    return bin_path


@cli.command()
def mypy(verbose: bool = True):
    """Run Mypy (configured in pyproject.toml)"""
    verbose_check_call(which('mypy'), '.', cwd=PACKAGE_ROOT, verbose=verbose, exit_on_error=True)


@cli.command()
def coverage(verbose: bool = True):
    """
    Run and show coverage.
    """
    coverage_bin = which('coverage')
    verbose_check_call(coverage_bin, 'run', verbose=verbose, exit_on_error=True)
    verbose_check_call(
        coverage_bin, 'report', '--fail-under=50', verbose=verbose, exit_on_error=True
    )
    verbose_check_call(coverage_bin, 'json', verbose=verbose, exit_on_error=True)


@cli.command()
def install():
    """
    Run pip-sync and install 'manageprojects' via pip as editable.
    """
    pip_sync_bin = which('pip-sync')
    pip_bin = which('pip')
    verbose_check_call(pip_sync_bin, PACKAGE_ROOT / 'requirements' / 'develop.txt')
    verbose_check_call(pip_bin, 'install', '-e', '.')


@cli.command()
def update():
    """
    Update the development environment by calling:
    - pip-compile production.in develop.in -> develop.txt
    - pip-compile production.in -> production.txt
    - pip-sync develop.txt
    """
    base_command = [
        which('pip-compile'),
        '--verbose',
        '--upgrade',
        '--allow-unsafe',
        '--generate-hashes',
        'requirements/production.in',
    ]
    verbose_check_call(  # develop + production
        *base_command,
        'requirements/develop.in',
        '--output-file',
        'requirements/develop.txt',
    )
    verbose_check_call(  # production only
        *base_command,
        '--output-file',
        'requirements/production.txt',
    )
    verbose_check_call(which('pip-sync'), 'requirements/develop.txt')
    install()


@cli.command()
def version(no_color: bool = False):
    """Print version and exit"""
    if no_color:
        rich.reconfigure(no_color=True)

    print('manageprojects v', end='')
    from manageprojects import __version__

    print(__version__, end=' ')

    git = Git(cwd=PACKAGE_ROOT)
    current_hash = git.get_current_hash(verbose=False)
    print(current_hash)


@cli.command()
def start_project(
    template: str,  # CookieCutter Template path or GitHub url
    output_dir: Path,  # Target path where CookieCutter should store the result files
    directory: Optional[str] = None,  # Directory name of the CookieCutter Template
    checkout: Optional[str] = None,
    no_input: bool = False,
    replay: bool = False,
    password: Optional[str] = None,  # Optional password to use when extracting the repository
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
):
    """
    Start a new "managed" project via a CookieCutter Template
    """
    log_config()
    print(f'Start project with template: {template!r}')
    print(f'Destination: {output_dir}')
    if output_dir.exists():
        print(f'Error: Destination "{output_dir}" already exists')
        sys.exit(1)
    if not output_dir.parent.is_dir():
        print(f'Error: Destination parent "{output_dir.parent}" does not exists')
        sys.exit(1)

    result: CookiecutterResult = start_managed_project(
        template=template,
        checkout=checkout,
        output_dir=output_dir,
        no_input=no_input,
        replay=replay,
        password=password,
        directory=directory,
        config_file=config_file,
    )

    print(
        f'CookieCutter template {template!r}'
        f' with git hash {result.git_hash}'
        f' was created here: {output_dir}'
    )
    return result


@cli.command()
def update_project(
    project_path: Path,
    password: Optional[str] = None,  # Optional password to use when extracting the repository
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
    cleanup: bool = True,  # Cleanup created files in /tmp/
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
):
    """
    Update a existing project.
    """
    log_config()
    update_managed_project(
        project_path=project_path,
        password=password,
        config_file=config_file,
        cleanup=cleanup,
        no_input=no_input,
    )


@cli.command()
def clone_project(
    project_path: Path,
    destination: Path,
    checkout: Optional[str] = None,  # Optional branch, tag or commit ID to checkout after clone
    password: Optional[str] = None,  # Optional password to use when extracting the repository
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
):
    """
    Clone a existing project by replay the cookiecutter template in a new directory.
    """
    log_config()
    return clone_managed_project(
        project_path=project_path,
        destination=destination,
        checkout=checkout,
        password=password,
        config_file=config_file,
        no_input=no_input,
    )


@cli.command()
def wiggle(project_path: Path, words: bool = False):
    """
    Run wiggle to merge *.rej in given directory.
    https://github.com/neilbrown/wiggle
    """
    wiggle_bin = shutil.which('wiggle')
    if not wiggle_bin:
        print('Error: "wiggle" can not be found!')
        print('Hint: sudo apt get install wiggle')
        sys.exit(1)

    assert_is_dir(project_path)

    args = [wiggle_bin, '--merge']
    if words:
        args.append('--words')
    args.append('--replace')

    for rej_file_path in project_path.rglob('*.rej'):
        real_file_path = rej_file_path.with_suffix('')
        if not real_file_path.is_file():
            print(f'Error real file "{real_file_path}" from "{rej_file_path}" not found. Skip.')
            continue
        try:
            verbose_check_call(
                *args,
                real_file_path,
                rej_file_path,
                verbose=True,
                exit_on_error=False,
            )
        except subprocess.CalledProcessError:
            continue


@cli.command()
def publish():
    """
    Build and upload this project to PyPi
    """
    log_config()
    test()  # Don't publish a broken state

    git = Git(cwd=PACKAGE_ROOT, detect_root=True)

    # TODO: Add the checks from:
    #       https://github.com/jedie/poetry-publish/blob/main/poetry_publish/publish.py

    twine_bin = which('twine')

    dist_path = PACKAGE_ROOT / 'dist'
    if dist_path.exists():
        shutil.rmtree(dist_path)

    verbose_check_call(sys.executable, '-m', 'build')
    verbose_check_call(twine_bin, 'check', 'dist/*')

    git_tag = f'v{manageprojects.__version__}'
    print('\ncheck git tag')
    git_tags = git.tag_list()
    if git_tag in git_tags:
        print(f'\n *** ERROR: git tag {git_tag!r} already exists!')
        print(git_tags)
        sys.exit(3)
    else:
        print('OK')

    verbose_check_call(twine_bin, 'upload', 'dist/*')

    git.tag(git_tag, message=f'publish version {git_tag}')
    print('\ngit push tag to server')
    git.push(tags=True)


def _call_darker(*, argv):
    # Work-a-round for:
    #
    #   File ".../site-packages/darker/linting.py", line 148, in _check_linter_output
    #     with Popen(  # nosec
    #   ...
    #   File "/usr/lib/python3.10/subprocess.py", line 1845, in _execute_child
    #     raise child_exception_type(errno_num, err_msg, err_filename)
    # FileNotFoundError: [Errno 2] No such file or directory: 'flake8'
    #
    # Just add .venv/bin/ to PATH:
    venv_path = PACKAGE_ROOT / '.venv' / 'bin'

    assert_is_dir(venv_path)
    assert_is_file(venv_path / 'flake8')
    venv_path = str(venv_path)
    if venv_path not in os.environ['PATH']:
        os.environ['PATH'] = venv_path + os.pathsep + os.environ['PATH']

    darker_main(argv=argv)


@cli.command()
def fix_code_style():
    """
    Fix code style via darker
    """
    _call_darker(argv=['--color'])


@cli.command()
def check_code_style(verbose: bool = True):
    _call_darker(argv=['--color', '--check'])
    if verbose:
        argv = ['--verbose']
    else:
        argv = []

    flake8_main(argv=argv)


@cli.command()  # Just add this command to help page
def test():
    """
    Run unittests
    """
    # Use the CLI from unittest module and pass all args to it:
    verbose_check_call(sys.executable, '-m', 'unittest', *sys.argv[2:])


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == 'test':
        # Just use the CLI from unittest with all available options and origin --help output ;)
        return test()
    else:
        cli()
