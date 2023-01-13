import os
import sys
from pathlib import Path

from bx_py_utils.path import assert_is_file

from manageprojects.utilities.subprocess_utils import verbose_check_call


def _call_darker(*args, package_root: Path, color: bool = True, verbose: bool = False):
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
        extra_env = dict(PATH=venv_path + os.pathsep + os.environ['PATH'])
    else:
        extra_env = None

    final_args = ['darker']
    if verbose:
        final_args.append('--verbose')
    if color:
        final_args.append('--color')

    final_args += list(args)

    verbose_check_call(
        *final_args,
        cwd=package_root,
        extra_env=extra_env,
        exit_on_error=True,
    )


def fix(package_root: Path, color: bool = True, verbose: bool = False):
    """
    Fix code style via darker
    """
    _call_darker(color=color, verbose=verbose, package_root=package_root)
    print('Code style fixed, OK.')
    sys.exit(0)


def check(package_root: Path, color: bool = True, verbose: bool = False):
    """
    Check code style by calling darker + flake8
    """
    _call_darker('--check', color=color, verbose=verbose, package_root=package_root)

    if verbose:
        args = ['--verbose']
    else:
        args = []

    verbose_check_call(
        'flake8',
        *args,
        cwd=package_root,
        exit_on_error=True,
    )
    print('Code style: OK')
    sys.exit(0)
