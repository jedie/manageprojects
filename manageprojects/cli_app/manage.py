"""
    CLI for usage
"""

from __future__ import annotations

import logging
from pathlib import Path
import shutil
import subprocess
import sys

from bx_py_utils.path import assert_is_dir
from cli_base.cli_tools.subprocess_utils import verbose_check_call
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE
from cli_base.cli_tools.version_info import print_version
from cli_base.click_defaults import (
    ARGUMENT_EXISTING_DIR,
    ARGUMENT_EXISTING_FILE,
    ARGUMENT_NOT_EXISTING_DIR,
    OPTION_ARGS_DEFAULT_FALSE,
    OPTION_ARGS_DEFAULT_TRUE,
)
from rich import print  # noqa
import rich_click as click

import manageprojects
from manageprojects.cli_app import cli
from manageprojects.constants import (
    FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
    FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION,
)
from manageprojects.cookiecutter_templates import (
    clone_managed_project,
    reverse_managed_project,
    start_managed_project,
    update_managed_project,
)
from manageprojects.data_classes import CookiecutterResult
from manageprojects.format_file import format_one_file
from manageprojects.utilities.log_utils import log_config


logger = logging.getLogger(__name__)


@cli.command()
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
    directory: str | None,
    checkout: str | None,
    input: bool,
    replay: bool,
    password: str | None,
    config_file: Path | None,
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

    print(f'CookieCutter template {template!r}' f' with git hash {result.git_hash}' f' was created here: {output_dir}')
    return result


cli.add_command(start_project)


@cli.command()
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
    password: str | None,
    config_file: Path | None,
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


@cli.command()
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
    checkout: str | None = None,
    password: str | None = None,
    config_file: Path | None = None,
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


@cli.command()
@click.argument('project_path', **ARGUMENT_EXISTING_DIR)
@click.argument('destination', **ARGUMENT_NOT_EXISTING_DIR)
@click.option(
    '--overwrite/--no-overwrite',
    **OPTION_ARGS_DEFAULT_FALSE,
    help='Overwrite existing files.',
)
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def reverse(
    project_path: Path,
    destination: Path,
    overwrite: bool,
    verbosity: int,
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
        verbosity=verbosity,
    )


cli.add_command(reverse)


@cli.command()
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


@cli.command()
@click.option(
    '--py-version',
    default=FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION,
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
@click.argument('file_path', **ARGUMENT_EXISTING_FILE)
def format_file(
    *,
    py_version: str,
    max_line_length: int,
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
        file_path=file_path,
    )


cli.add_command(format_file)


@cli.command()
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)


cli.add_command(version)


def main():
    print_version(manageprojects)

    # Execute Click CLI:
    cli.name = './cli.py'
    cli()
