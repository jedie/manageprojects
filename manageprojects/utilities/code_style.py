import sys
import warnings
from pathlib import Path

from cli_base.cli_tools.subprocess_utils import ToolsExecutor, verbose_check_call


def _call_darker(*args, package_root: Path, color: bool = True, verbose: bool = False):

    final_args = ['darker']
    if verbose:
        final_args.append('--verbose')
    if color:
        final_args.append('--color')

    final_args += list(args)

    tools_executor = ToolsExecutor(cwd=package_root)
    tools_executor.verbose_check_call(
        *final_args,
        exit_on_error=True,
    )


def fix(package_root: Path, color: bool = True, verbose: bool = False):
    """
    Fix code style via darker
    """
    warnings.warn(
        'Migrate to: cli_base.cli_tools.code_style.fix !',
        DeprecationWarning,
        stacklevel=2,
    )
    _call_darker(color=color, verbose=verbose, package_root=package_root)
    print('Code style fixed, OK.')
    sys.exit(0)


def check(package_root: Path, color: bool = True, verbose: bool = False):
    """
    Check code style by calling darker + flake8
    """
    warnings.warn(
        'Migrate to: cli_base.cli_tools.code_style.check !',
        DeprecationWarning,
        stacklevel=2,
    )
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
