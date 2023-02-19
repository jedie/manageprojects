import os
import shutil
import subprocess
import sys
from pathlib import Path

from bx_py_utils.path import assert_is_dir, assert_is_file
from rich import print  # noqa


DEFAULT_TIMEOUT = 5 * 60


def make_absolute_path(path):
    """
    Resolve the path, but not for symlinks.
    e.g.: '.venv/bin/python' is a symlink to e.g.: '/usr/bin/python3.x'
    We would like to keep the origin symlink ;)
    """
    if not isinstance(path, Path):
        path = Path(path)

    if path.is_symlink():
        path = path.absolute()
    else:
        path = path.resolve(strict=True)

    return path


def make_relative_path(path, relative_to):
    """
    Makes {path} relative to {relative_to}, if possible.
    """
    path = make_absolute_path(path=path)
    relative_to = make_absolute_path(path=relative_to)

    try:
        is_relative_to = path.is_relative_to(relative_to)
    except AttributeError:  # is_relative_to() is new in Python 3.9
        try:
            path = path.relative_to(relative_to)
        except ValueError:
            # {path} doesn't start with {relative_to} -> do nothing
            pass
    else:
        if is_relative_to:
            path = path.relative_to(relative_to)

    return path


def _print_info(popenargs, *, cwd, kwargs):
    print()
    print('_' * 100)

    if len(popenargs) > 1:
        command, *args = popenargs
    else:
        command = popenargs[0]
        args = []

    command_path = make_relative_path(Path(command), relative_to=cwd)

    command_name = command_path.name
    command_dir = command_path.parent

    print(f'[white]{cwd}[/white][bold]$[/bold]', end=' ')

    if command_dir and command_dir != Path.cwd():
        print(f'[green]{command_dir}{os.sep}[/green]', end='')

    if command_name:
        print(f'[yellow bold]{command_name}[/yellow bold]', end='')

    for arg in args:
        if isinstance(arg, str):
            if arg.startswith('--'):
                print(f' [magenta]{arg}[/magenta]', end='')
                continue
            elif arg.startswith('-'):
                print(f' [cyan]{arg}[/cyan]', end='')
                continue

        print(f' [blue]{arg}[/blue]', end='')

    if kwargs:
        verbose_kwargs = ', '.join(f'{k}={v!r}' for k, v in sorted(kwargs.items()))
        print(f' (kwargs: {verbose_kwargs})', end='')

    print('\n', flush=True)


def prepare_popenargs(popenargs, cwd=None):
    if cwd is None:
        cwd = Path.cwd()
    else:
        assert_is_dir(cwd)

    command_path = Path(popenargs[0])
    if not command_path.is_file():
        # Lookup in current venv bin path first:
        bin_path = str(Path(sys.executable).parent.absolute())
        command = shutil.which(str(command_path), path=bin_path)
        if not command:
            # Search in PATH for this command that doesn't point to a existing file:
            command = shutil.which(str(command_path))
            if not command:
                raise FileNotFoundError(f'Command "{popenargs[0]}" not found in PATH!')

        command = make_absolute_path(path=command)

        # Replace command name with full path:
        popenargs = list(popenargs)
        popenargs[0] = command

    return popenargs, cwd


def verbose_check_call(
    *popenargs,
    verbose=True,
    cwd=None,
    extra_env=None,
    exit_on_error=False,
    timeout=DEFAULT_TIMEOUT,
    env=None,
    **kwargs,
):
    """'verbose' version of subprocess.check_call()"""

    popenargs, cwd = prepare_popenargs(popenargs, cwd=cwd)

    if verbose:
        _print_info(popenargs, cwd=cwd, kwargs=kwargs)

    if env is None:
        env = os.environ.copy()

    if extra_env:
        env.update(extra_env)

    try:
        return subprocess.check_call(
            [str(part) for part in popenargs],  # e.g.: Path() instance -> str,
            text=True,
            env=env,
            cwd=cwd,
            timeout=timeout,
            **kwargs,
        )
    except subprocess.CalledProcessError as err:
        if verbose:
            print(f'[red]Process "{popenargs[0]}" finished with exit code {err.returncode!r}[/red]')
        if exit_on_error:
            sys.exit(err.returncode)
        raise


def verbose_check_output(
    *popenargs,
    verbose=True,
    cwd=None,
    extra_env=None,
    exit_on_error=False,
    timeout=DEFAULT_TIMEOUT,
    env=None,
    **kwargs,
):
    """'verbose' version of subprocess.check_output()"""

    popenargs, cwd = prepare_popenargs(popenargs, cwd=cwd)

    if verbose:
        _print_info(popenargs, cwd=cwd, kwargs=kwargs)

    if env is None:
        env = os.environ.copy()

    if extra_env:
        env.update(extra_env)

    try:
        output = subprocess.check_output(
            [str(part) for part in popenargs],  # e.g.: Path() instance -> str,
            text=True,
            env=env,
            cwd=cwd,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            **kwargs,
        )
    except subprocess.CalledProcessError as err:
        if exit_on_error:
            print('-' * 79)
            print(err.stdout)
            print('-' * 79)
            print(f'[red]Process "{popenargs[0]}" finished with exit code {err.returncode!r}[/red]')
            sys.exit(err.returncode)
        raise
    else:
        return output


class ToolsExecutor:
    def __init__(self, cwd: Path):
        self.cwd = cwd

        self.bin_path = Path(sys.executable).parent
        self.extra_env = {}

        bin_path_str = str(self.bin_path)
        if bin_path_str not in os.environ['PATH']:
            self.extra_env['PATH'] = bin_path_str + os.pathsep + os.environ['PATH']

        self.extra_env['PYTHONUNBUFFERED'] = '1'

    def verbose_check_output(self, bin, *popenargs, verbose=True, exit_on_error=True, **kwargs):
        """'verbose' version of subprocess.check_output()"""
        bin_path = str(self.bin_path / bin)
        assert_is_file(bin_path)

        try:
            verbose_check_call(
                bin_path,
                *popenargs,
                verbose=verbose,
                cwd=self.cwd,
                extra_env=self.extra_env,
                exit_on_error=exit_on_error,
                **kwargs,
            )
        except subprocess.CalledProcessError:
            pass
