import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import rich_click as click
from bx_py_utils.path import assert_is_dir, assert_is_file
from rich import print  # noqa
from rich_click import RichGroup

import manageprojects
from manageprojects import constants
from manageprojects.constants import (
    FORMAT_PY_FILE_DARKER_PRE_FIXES,
    FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
    FORMAT_PY_FILE_DEFAULT_MIN_PYTON_VERSION,
)
from manageprojects.cookiecutter_templates import (
    clone_managed_project,
    reverse_managed_project,
    start_managed_project,
    update_managed_project,
)
from manageprojects.data_classes import CookiecutterResult
from manageprojects.format_file import format_one_file
from manageprojects.utilities import code_style
from manageprojects.utilities.log_utils import log_config
from manageprojects.utilities.publish import publish_package
from manageprojects.utilities.subprocess_utils import verbose_check_call
from manageprojects.utilities.version_info import print_version


logger = logging.getLogger(__name__)


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')

OPTION_ARGS_DEFAULT_TRUE = dict(is_flag=True, show_default=True, default=True)
OPTION_ARGS_DEFAULT_FALSE = dict(is_flag=True, show_default=True, default=False)
ARGUMENT_EXISTING_DIR = dict(
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path)
)
ARGUMENT_NOT_EXISTING_DIR = dict(
    type=click.Path(exists=False, file_okay=False, dir_okay=True, readable=False, writable=True, path_type=Path)
)
ARGUMENT_EXISTING_FILE = dict(
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path)
)


class ClickGroup(RichGroup):  # FIXME: How to set the "info_name" easier?
    def make_context(self, info_name, *args, **kwargs):
        info_name = './cli.py'
        return super().make_context(info_name, *args, **kwargs)


@click.group(
    cls=ClickGroup,
    epilog=constants.CLI_EPILOG,
)
def cli():
    pass


@click.command()
@click.option('--verbose/--no-verbose', **OPTION_ARGS_DEFAULT_FALSE)
def mypy(verbose: bool = True):
    """Run Mypy (configured in pyproject.toml)"""
    verbose_check_call('mypy', '.', cwd=PACKAGE_ROOT, verbose=verbose, exit_on_error=True)


cli.add_command(mypy)


@click.command()
@click.option('--verbose/--no-verbose', **OPTION_ARGS_DEFAULT_FALSE)
def coverage(verbose: bool = True):
    """
    Run and show coverage.
    """
    verbose_check_call('coverage', 'run', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'combine', '--append', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'report', '--fail-under=50', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'xml', verbose=verbose, exit_on_error=True)
    verbose_check_call('coverage', 'json', verbose=verbose, exit_on_error=True)


cli.add_command(coverage)


@click.command()
def install():
    """
    Run pip-sync and install 'manageprojects' via pip as editable.
    """
    verbose_check_call('pip-sync', PACKAGE_ROOT / 'requirements.dev.txt')
    verbose_check_call('pip', 'install', '--no-deps', '-e', '.')


cli.add_command(install)


@click.command()
def safety():
    """
    Run safety check against current requirements files
    """
    verbose_check_call('safety', 'check', '-r', 'requirements.dev.txt')


cli.add_command(safety)


@click.command()
def update():
    """
    Update "requirements*.txt" dependencies files
    """
    bin_path = Path(sys.executable).parent

    verbose_check_call(bin_path / 'pip', 'install', '-U', 'pip')
    verbose_check_call(bin_path / 'pip', 'install', '-U', 'pip-tools')

    extra_env = dict(
        CUSTOM_COMPILE_COMMAND='./cli.py update',
    )

    pip_compile_base = [
        bin_path / 'pip-compile',
        '--verbose',
        '--allow-unsafe',  # https://pip-tools.readthedocs.io/en/latest/#deprecations
        '--resolver=backtracking',  # https://pip-tools.readthedocs.io/en/latest/#deprecations
        '--upgrade',
        '--generate-hashes',
    ]

    # Only "prod" dependencies:
    verbose_check_call(
        *pip_compile_base,
        'pyproject.toml',
        '--output-file',
        'requirements.txt',
        extra_env=extra_env,
    )

    # dependencies + "dev"-optional-dependencies:
    verbose_check_call(
        *pip_compile_base,
        'pyproject.toml',
        '--extra=dev',
        '--output-file',
        'requirements.dev.txt',
        extra_env=extra_env,
    )

    verbose_check_call(bin_path / 'safety', 'check', '-r', 'requirements.dev.txt')

    # Install new dependencies in current .venv:
    verbose_check_call(bin_path / 'pip-sync', 'requirements.dev.txt')


cli.add_command(update)


@click.command()
@click.argument('template')
@click.argument('output_dir', **ARGUMENT_NOT_EXISTING_DIR)
@click.option(
    '--directory',
    default=None,
    help=(
        'Cookiecutter Option: Directory within repo that holds cookiecutter.json file'
        ' for advanced repositories with multi templates in it'
    ),
)
@click.option(
    '--checkout',
    default=None,
    help='Cookiecutter Option: branch, tag or commit to checkout after git clone',
)
@click.option(
    '--input/--no-input',
    **OPTION_ARGS_DEFAULT_TRUE,
    help=('Cookiecutter Option: Do not prompt for parameters' ' and only use cookiecutter.json file content'),
)
@click.option(
    '--replay/--no-replay',
    **OPTION_ARGS_DEFAULT_FALSE,
    help=('Cookiecutter Option: Do not prompt for parameters' ' and only use information entered previously'),
)
@click.option(
    '--password',
    default=None,
    help='Cookiecutter Option: Password to use when extracting the repository',
)
@click.option(
    '--config-file',
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"',
)
def start_project(
    template: str,
    output_dir: Path,
    directory: Optional[str],
    checkout: Optional[str],
    input: bool,
    replay: bool,
    password: Optional[str],
    config_file: Optional[Path],
):
    """
    Start a new "managed" project via a CookieCutter Template.
    Note: The CookieCutter Template *must* be use git!

    e.g.:

    ./cli.py start-project https://github.com/jedie/cookiecutter_templates/ --directory piptools-python ~/foobar/
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
        input=input,
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


cli.add_command(start_project)


@click.command()
@click.argument('project_path', **ARGUMENT_EXISTING_DIR)
@click.option(
    '--overwrite/--no-overwrite',
    **OPTION_ARGS_DEFAULT_TRUE,
    help=(
        'Overwrite all Cookiecutter template files to the last template state and'
        ' do not apply the changes via git patches.'
        ' The developer is supposed to apply the differences manually via git.'
        ' Will be aborted if the project git repro is not in a clean state.'
    ),
)
@click.option(
    '--password',
    default=None,
    help='Cookiecutter Option: Password to use when extracting the repository',
)
@click.option(
    '--config-file',
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"',
)
@click.option(
    '--input/--no-input',
    **OPTION_ARGS_DEFAULT_FALSE,
    help='Cookiecutter Option: Do not prompt for parameters and only use cookiecutter.json file content',
)
@click.option(
    '--cleanup/--no-cleanup',
    **OPTION_ARGS_DEFAULT_TRUE,
    help='Cleanup created temporary files',
)
def update_project(
    project_path: Path,
    overwrite: bool,
    password: Optional[str],
    config_file: Optional[Path],
    input: bool,
    cleanup: bool,
):
    """
    Update a existing project.

    e.g. update by overwrite (and merge changes manually via git):

    ./cli.py update-project ~/foo/bar/
    """
    log_config()
    print(f'Update project: "{project_path}"...')
    update_managed_project(
        project_path=project_path,
        overwrite=overwrite,
        password=password,
        config_file=config_file,
        cleanup=cleanup,
        input=input,
    )
    print(f'Managed project "{project_path}" updated, ok.')


cli.add_command(update_project)


@click.command()
@click.argument('project_path', **ARGUMENT_EXISTING_DIR)
@click.argument('output_dir', **ARGUMENT_NOT_EXISTING_DIR)
@click.option(
    '--password',
    default=None,
    help='Cookiecutter Option: Password to use when extracting the repository',
)
@click.option(
    '--config-file',
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"',
)
@click.option(
    '--input/--no-input',
    **OPTION_ARGS_DEFAULT_FALSE,
    help=('Cookiecutter Option: Do not prompt for parameters' ' and only use cookiecutter.json file content'),
)
def clone_project(
    project_path: Path,
    output_dir: Path,
    input: bool,
    checkout: Optional[str] = None,
    password: Optional[str] = None,
    config_file: Optional[Path] = None,
):
    """
    Clone existing project by replay the cookiecutter template in a new directory.

    e.g.:

    ./cli.py clone-project ~/foo/bar ~/cloned/
    """
    print(locals())
    log_config()
    return clone_managed_project(
        project_path=project_path,
        destination=output_dir,
        checkout=checkout,
        password=password,
        config_file=config_file,
        input=input,
    )


cli.add_command(clone_project)


@click.command()
@click.argument('project_path', **ARGUMENT_EXISTING_DIR)
@click.argument('destination', **ARGUMENT_NOT_EXISTING_DIR)
@click.option(
    '--overwrite/--no-overwrite',
    **OPTION_ARGS_DEFAULT_FALSE,
    help='Overwrite existing files.',
)
def reverse(
    project_path: Path,
    destination: Path,
    overwrite: bool,
):
    """
    Create a cookiecutter template from a managed project.

    e.g.:

    ./cli.py reverse ~/my_managed_project/ ~/my_new_cookiecutter_template/
    """
    log_config()
    return reverse_managed_project(
        project_path=project_path,
        destination=destination,
        overwrite=overwrite,
    )


cli.add_command(reverse)


@click.command()
@click.argument('project_path', **ARGUMENT_EXISTING_DIR)
@click.option(
    '--words/--no-words',
    **OPTION_ARGS_DEFAULT_FALSE,
    help='wiggle Option: word-wise diff and merge.',
)
def wiggle(project_path: Path, words: bool):
    """
    Run wiggle to merge *.rej in given directory.
    https://github.com/neilbrown/wiggle

    e.g.:

    ./cli.py wiggle ~/my_managed_project/
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


cli.add_command(wiggle)


@click.command()
def publish():
    """
    Build and upload this project to PyPi
    """
    verbose_check_call('pip', 'install', '-e', '.')  # Auto fix: Maybe the current version is not installed ;)

    _run_unittest_cli(verbose=False, exit_after_run=False)  # Don't publish a broken state

    publish_package(
        module=manageprojects,
        package_path=PACKAGE_ROOT,
    )


cli.add_command(publish)


@click.command()
@click.option('--color/--no-color', **OPTION_ARGS_DEFAULT_TRUE)
@click.option('--verbose/--no-verbose', **OPTION_ARGS_DEFAULT_FALSE)
def fix_code_style(color: bool = True, verbose: bool = False):
    """
    Fix code style of all manageprojects source code files via darker
    """
    code_style.fix(package_root=PACKAGE_ROOT, color=color, verbose=verbose)


cli.add_command(fix_code_style)


@click.command()
@click.option('--color/--no-color', **OPTION_ARGS_DEFAULT_TRUE)
@click.option('--verbose/--no-verbose', **OPTION_ARGS_DEFAULT_FALSE)
def check_code_style(color: bool = True, verbose: bool = False):
    """
    Check code style by calling darker + flake8
    """
    code_style.check(package_root=PACKAGE_ROOT, color=color, verbose=verbose)


cli.add_command(check_code_style)


@click.command()
def update_test_snapshot_files():
    """
    Update all test snapshot files (by remove and recreate all snapshot files)
    """

    def iter_snapshot_files():
        yield from PACKAGE_ROOT.rglob('*.snapshot.*')

    removed_file_count = 0
    for item in iter_snapshot_files():
        item.unlink()
        removed_file_count += 1
    print(f'{removed_file_count} test snapshot files removed... run tests...')

    # Just recreate them by running tests:
    _run_unittest_cli(
        extra_env=dict(
            RAISE_SNAPSHOT_ERRORS='0',  # Recreate snapshot files without error
        ),
        verbose=False,
        exit_after_run=False,
    )

    new_files = len(list(iter_snapshot_files()))
    print(f'{new_files} test snapshot files created, ok.\n')


cli.add_command(update_test_snapshot_files)


def _run_unittest_cli(extra_env=None, verbose=True, exit_after_run=True):
    """
    Call the origin unittest CLI and pass all args to it.
    """
    if extra_env is None:
        extra_env = dict()

    extra_env.update(
        dict(
            PYTHONUNBUFFERED='1',
            PYTHONWARNINGS='always',
        )
    )

    args = sys.argv[2:]
    if not args:
        if verbose:
            args = ('--verbose', '--locals', '--buffer')
        else:
            args = ('--locals', '--buffer')

    verbose_check_call(
        sys.executable,
        '-m',
        'unittest',
        *args,
        timeout=15 * 60,
        extra_env=extra_env,
    )
    if exit_after_run:
        sys.exit(0)


cli.add_command(update_test_snapshot_files)


@click.command()  # Dummy command
def test():
    """
    Run unittests
    """
    _run_unittest_cli()


cli.add_command(test)


def _run_tox():
    verbose_check_call(sys.executable, '-m', 'tox', *sys.argv[2:])
    sys.exit(0)


@click.command()  # Dummy "tox" command
def tox():
    """
    Run tox
    """
    _run_tox()


cli.add_command(tox)


@click.command()
@click.option(
    '--py-version',
    default=FORMAT_PY_FILE_DEFAULT_MIN_PYTON_VERSION,
    show_default=True,
    help='Fallback Python version for darker/pyupgrade, if version is not defined in pyproject.toml',
)
@click.option(
    '-l',
    '--max-line-length',
    default=FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
    type=int,
    show_default=True,
    help='Fallback max. line length for darker/isort etc., if not defined in .editorconfig',
)
@click.option(
    '--darker-prefixes',
    default=FORMAT_PY_FILE_DARKER_PRE_FIXES,
    show_default=True,
    help='Apply prefixes via autopep8 before calling darker.',
)
@click.argument('file_path', **ARGUMENT_EXISTING_FILE)
def format_file(
    *,
    py_version: str,
    max_line_length: int,
    darker_prefixes: str,
    file_path: Path,
):
    """
    Format and check the given python source code file with darker/autoflake/isort/pyupgrade/autopep8/mypy etc.

    The optional fallback values will be only used, if we can't get them from the project meta files
    like ".editorconfig" and "pyproject.toml"
    """
    format_one_file(
        default_min_py_version=py_version,
        default_max_line_length=max_line_length,
        darker_prefixes=darker_prefixes,
        file_path=file_path,
    )


cli.add_command(format_file)


@click.command()
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)


cli.add_command(version)


def main():
    print_version(manageprojects)

    if len(sys.argv) >= 2:
        # Check if we just pass a command call
        command = sys.argv[1]
        if command == 'test':
            _run_unittest_cli()
        elif command == 'tox':
            _run_tox()

    # Execute Click CLI:
    cli.name = './cli.py'
    cli()
