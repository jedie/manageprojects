"""
    CLI for usage
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

from bx_py_utils.path import assert_is_dir
from cli_base.cli_tools.subprocess_utils import verbose_check_call
from cli_base.tyro_commands import TyroVerbosityArgType
from rich import print  # noqa
from tyro.conf import arg

from manageprojects.cli_app import app
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


@app.command
def start_project(
    template: Annotated[
        str,
        arg(help='The name of the CookieCutter Template.'),
    ],
    output_dir: Annotated[
        Path,
        arg(help='Target path for the new project. Must not exist yet!'),
    ],
    /,
    verbosity: TyroVerbosityArgType,
    #
    # Cookiecutter options:
    directory: Annotated[
        str | None,
        arg(
            help=(
                'Cookiecutter Option: Directory within repo that holds cookiecutter.json file'
                ' for advanced repositories with multi templates in it'
            )
        ),
    ] = None,
    replay: Annotated[
        bool,
        arg(help='Cookiecutter Option: Do not prompt for parameters and only use information entered previously'),
    ] = False,
    input: Annotated[
        bool,
        arg(help='Cookiecutter Option: Do not prompt for parameters and only use cookiecutter.json file content'),
    ] = False,
    checkout: Annotated[
        str | None,
        arg(help='Cookiecutter Option: Optional branch, tag or commit ID to checkout after clone'),
    ] = None,
    password: Annotated[
        str | None,
        arg(help='Cookiecutter Option: Password to use when extracting the repository'),
    ] = None,
    config_file: Annotated[
        Path | None,
        arg(help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"'),
    ] = None,
):
    """
    Start a new "managed" project via a CookieCutter Template.
    Note: The CookieCutter Template *must* be use git!

    e.g.:

    ./cli.py start-project https://github.com/jedie/cookiecutter_templates/ --directory piptools-python ~/foobar/
    """
    log_config(verbosity, log_in_file=True)
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


@app.command
def update_project(
    project_path: Path,
    /,
    verbosity: TyroVerbosityArgType,
    overwrite: Annotated[
        bool,
        arg(
            help=(
                'Overwrite all Cookiecutter template files to the last template state and'
                ' do not apply the changes via git patches.'
                ' The developer is supposed to apply the differences manually via git.'
                ' Will be aborted if the project git repro is not in a clean state.'
            )
        ),
    ] = True,
    cleanup: Annotated[
        bool,
        arg(help='Cleanup created temporary files'),
    ] = True,
    #
    # Cookiecutter options:
    input: Annotated[
        bool,
        arg(help='Cookiecutter Option: Do not prompt for parameters and only use cookiecutter.json file content'),
    ] = False,
    password: Annotated[
        str | None,
        arg(help='Cookiecutter Option: Password to use when extracting the repository'),
    ] = None,
    config_file: Annotated[
        Path | None,
        arg(help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"'),
    ] = None,
):
    """
    Update a existing project.

    e.g. update by overwrite (and merge changes manually via git):

    ./cli.py update-project ~/foo/bar/
    """
    log_config(verbosity, log_in_file=True)
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


@app.command
def clone_project(
    project_path: Annotated[
        Path,
        arg(help='Source project that should be cloned. Must be a managed project!'),
    ],
    output_dir: Annotated[
        Path,
        arg(help='Destination of the cloned project. Must not exist yet!'),
    ],
    /,
    verbosity: TyroVerbosityArgType,
    #
    # Cookiecutter options:
    input: Annotated[
        bool,
        arg(help='Cookiecutter Option: Do not prompt for parameters and only use cookiecutter.json file content'),
    ] = False,
    checkout: Annotated[
        str | None,
        arg(help='Cookiecutter Option: Optional branch, tag or commit ID to checkout after clone'),
    ] = None,
    password: Annotated[
        str | None,
        arg(help='Cookiecutter Option: Password to use when extracting the repository'),
    ] = None,
    config_file: Annotated[
        Path | None,
        arg(help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"'),
    ] = None,
):
    """
    Clone existing project by replay the cookiecutter template in a new directory.

    e.g.:

    ./cli.py clone-project ~/foo/bar ~/cloned/
    """
    log_config(verbosity=verbosity)
    return clone_managed_project(
        project_path=project_path,
        destination=output_dir,
        checkout=checkout,
        password=password,
        config_file=config_file,
        input=input,
    )


@app.command
def reverse(
    project_path: Path,
    destination: Path,
    /,
    verbosity: TyroVerbosityArgType,
    overwrite: Annotated[bool, arg(help='Overwrite existing files.')] = False,
):
    """
    Create a cookiecutter template from a managed project.

    e.g.:

    ./cli.py reverse ~/my_managed_project/ ~/my_new_cookiecutter_template/
    """
    log_config(verbosity)
    return reverse_managed_project(
        project_path=project_path,
        destination=destination,
        overwrite=overwrite,
        verbosity=verbosity,
    )


@app.command
def wiggle(
    project_path: Path,
    /,
    words: Annotated[bool, arg(help='wiggle Option: word-wise diff and merge.')] = False,
):
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


@app.command
def format_file(
    file_path: Path,
    /,
    verbosity: TyroVerbosityArgType,
    py_version: Annotated[
        str,
        arg(help='Fallback Python version for darker/pyupgrade, if version is not defined in pyproject.toml'),
    ] = FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION,
    max_line_length: Annotated[
        int,
        arg(help='Fallback max. line length for darker/isort etc., if not defined in .editorconfig'),
    ] = FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
):
    """
    Format and check the given python source code file with ruff, codespell and mypy.

    The optional fallback values will be only used, if we can't get them from the project meta files
    like ".editorconfig" and "pyproject.toml"
    """
    log_config(verbosity=verbosity, log_in_file=False)
    format_one_file(
        default_min_py_version=py_version,
        default_max_line_length=max_line_length,
        file_path=file_path,
    )


@app.command
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)
