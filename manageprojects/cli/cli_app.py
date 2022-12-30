import logging
import os
import shlex
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
from manageprojects import __version__
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


app = typer.Typer(
    name='./cli.py',
    epilog='Project Homepage: https://github.com/jedie/manageprojects',
)


@app.command()
def mypy(verbose: bool = True):
    """Run Mypy (configured in pyproject.toml)"""
    verbose_check_call('mypy', '.', cwd=PACKAGE_ROOT, verbose=verbose, exit_on_error=True)


@app.command()
def coverage(verbose: bool = True):
    """
    Run and show coverage.
    """
    verbose_check_call('coverage', 'run', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'report', '--fail-under=50', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'json', verbose=verbose, exit_on_error=True)


@app.command()
def install():
    """
    Run pip-sync and install 'manageprojects' via pip as editable.
    """
    verbose_check_call('pip-sync', PACKAGE_ROOT / 'requirements' / 'develop.txt')
    verbose_check_call('pip', 'install', '-e', '.')


@app.command()
def update():
    """
    Update the development environment by calling:
    - pip-compile production.in develop.in -> develop.txt
    - pip-compile production.in -> production.txt
    - pip-sync develop.txt
    """
    base_command = [
        'pip-compile',
        '--verbose',
        '--upgrade',
        '--allow-unsafe',
        '--generate-hashes',
        '--resolver=backtracking',
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
    verbose_check_call('pip-sync', 'requirements/develop.txt')


@app.command()
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


@app.command()
def start_project(
    template: str = typer.Argument(
        default=None,
        help='CookieCutter Template path or GitHub url. *Must* be a git based template!',
    ),
    output_dir: Path = typer.Argument(
        default=None,
        exists=False,
        file_okay=False,
        dir_okay=True,
        help='Target path where CookieCutter should store the result files',
    ),
    directory: Optional[str] = typer.Option(
        default=None,
        help=(
            'Cookiecutter Option: Directory within repo that holds cookiecutter.json file'
            ' for advanced repositories with multi templates in it'
        ),
    ),
    checkout: Optional[str] = typer.Option(
        default=None,
        help='Cookiecutter Option: branch, tag or commit to checkout after git clone',
    ),
    no_input: bool = typer.Option(
        False,
        '--no-input/--input',
        help=(
            'Cookiecutter Option: Do not prompt for parameters'
            ' and only use cookiecutter.json file content'
        ),
    ),
    replay: bool = typer.Option(
        default=False,
        help=(
            'Cookiecutter Option: Do not prompt for parameters'
            ' and only use information entered previously'
        ),
    ),
    password: Optional[str] = typer.Option(
        default=None,
        help='Cookiecutter Option: Password to use when extracting the repository',
    ),
    config_file: Optional[Path] = typer.Option(
        default=None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"',
    ),
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


@app.command()
def update_project(
    project_path: Path = typer.Argument(
        default=None,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help=(
            'Path to the project source code that should be update'
            ' with Cookiecutter template changes'
        ),
    ),
    password: Optional[str] = typer.Option(
        default=None,
        help='Cookiecutter Option: Password to use when extracting the repository',
    ),
    config_file: Optional[Path] = typer.Option(
        default=None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"',
    ),
    no_input: bool = typer.Option(
        False,
        '--no-input/--input',
        help=(
            'Cookiecutter Option: Do not prompt for parameters'
            ' and only use cookiecutter.json file content'
        ),
    ),
    cleanup: bool = typer.Option(default=True, help='Cleanup created temporary files'),
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


@app.command()
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


@app.command()
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


@app.command()
def publish():
    """
    Build and upload this project to PyPi
    """
    test()  # Don't publish a broken state

    git = Git(cwd=PACKAGE_ROOT, detect_root=True)

    # TODO: Add the checks from:
    #       https://github.com/jedie/poetry-publish/blob/main/poetry_publish/publish.py

    dist_path = PACKAGE_ROOT / 'dist'
    if dist_path.exists():
        shutil.rmtree(dist_path)

    verbose_check_call(sys.executable, '-m', 'build')
    verbose_check_call('twine', 'check', 'dist/*')

    git_tag = f'v{__version__}'
    print('\ncheck git tag')
    git_tags = git.tag_list()
    if git_tag in git_tags:
        print(f'\n *** ERROR: git tag {git_tag!r} already exists!')
        print(git_tags)
        sys.exit(3)
    else:
        print('OK')

    verbose_check_call('twine', 'upload', 'dist/*')

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
    venv_path = Path(sys.executable).parent
    assert_is_file(venv_path / 'flake8')
    assert_is_file(venv_path / 'darker')
    venv_path = str(venv_path)
    if venv_path not in os.environ['PATH']:
        os.environ['PATH'] = venv_path + os.pathsep + os.environ['PATH']

    print(f'Run "darker {shlex.join(str(part) for part in argv)}"...')
    exit_code = darker_main(argv=argv)
    print(f'darker exit code: {exit_code!r}')
    return exit_code


@app.command()
def fix_code_style():
    """
    Fix code style via darker
    """
    exit_code = _call_darker(argv=['--color'])
    sys.exit(exit_code)


@app.command()
def check_code_style(verbose: bool = True):
    darker_exit_code = _call_darker(argv=['--color', '--check'])
    if verbose:
        argv = ['--verbose']
    else:
        argv = []

    print(f'Run flake8 {shlex.join(str(part) for part in argv)}')
    flake8_exit_code = flake8_main(argv=argv)
    print(f'flake8 exit code: {flake8_exit_code!r}')
    sys.exit(max(darker_exit_code, flake8_exit_code))


@app.command()  # Just add this command to help page
def test():
    """
    Run unittests
    """
    args = sys.argv[2:]
    if not args:
        args = ('--verbose', '--locals', '--buffer')
    # Use the CLI from unittest module and pass all args to it:
    verbose_check_call(
        sys.executable,
        '-m',
        'unittest',
        *args,
        timeout=15 * 60,
        extra_env=dict(
            PYTHONUNBUFFERED='1',
            PYTHONWARNINGS='always',
        ),
    )


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == 'test':
        # Just use the CLI from unittest with all available options and origin --help output ;)
        return test()
    else:
        # Execute Typer App:
        app()
