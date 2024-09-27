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

from manageprojects.cli_app import cli
from manageprojects.constants import (
    FORMAT_PY_FILE_DARKER_PRE_FIXES,
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


InputType = Annotated[
    bool,
    arg(
        help=(
            'Cookiecutter Option: Do not prompt for user input.'
            ' Use default values for template parameters taken from `cookiecutter.json`.'
        )
    ),
]
ConfigFileType = Annotated[
    Path,
    arg(help='Cookiecutter Option: Optional path to "cookiecutter_config.yaml"'),
]
PasswordType = Annotated[
    str,
    arg(help='Cookiecutter Option: Password to use when extracting the repository'),
]
CheckoutType = Annotated[
    str,
    arg(help='Cookiecutter Option: Optional branch, tag or commit ID to checkout after clone'),
]


DirectoryType = Annotated[
    str,
    arg(
        help=(
            'Cookiecutter Option: Directory within repo that holds cookiecutter.json file'
            ' for advanced repositories with multi templates in it'
        )
    ),
]
ReplayType = Annotated[
    bool,
    arg(help='Cookiecutter Option: Do not prompt for parameters and only use cookiecutter.json file content'),
]


@cli.register
def start_project(
    template: str,
    /,
    output_dir: Path,
    directory: str | None = None,
    replay: ReplayType = False,
    config_file: ConfigFileType | None = None,
    password: PasswordType | None = None,
    checkout: CheckoutType | None = None,
    input: InputType = True,
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


OverwriteType = Annotated[
    bool,
    arg(
        help=(
            'Overwrite all Cookiecutter template files to the last template state and'
            ' do not apply the changes via git patches.'
            ' The developer is supposed to apply the differences manually via git.'
            ' Will be aborted if the project git repro is not in a clean state.'
        )
    ),
]
CleanupType = Annotated[
    bool,
    arg(help='Cleanup created temporary files'),
]


@cli.register
def update_project(
    project_path: Path,
    /,
    password: PasswordType | None,
    config_file: ConfigFileType | None,
    input: InputType,
    overwrite: OverwriteType = True,
    cleanup: CleanupType = True,
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


@cli.register
def clone_project(
    project_path: Path,
    output_dir: Path,
    /,
    input: InputType = False,
    checkout: CheckoutType | None = None,
    password: PasswordType | None = None,
    config_file: ConfigFileType | None = None,
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


OverwriteType = Annotated[
    bool,
    arg(help='Overwrite existing files.'),
]


@cli.register
def reverse(
    project_path: Path,
    destination: Path,
    /,
    verbosity: TyroVerbosityArgType,
    overwrite: OverwriteType = False,
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


WordsType = Annotated[
    bool,
    arg(help='wiggle Option: word-wise diff and merge.'),
]


@cli.register
def wiggle(project_path: Path, /, words: WordsType = False):
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


PyVersionType = Annotated[
    str,
    arg(help='Fallback Python version for darker/pyupgrade, if version is not defined in pyproject.toml'),
]
MaxLineLengthType = Annotated[
    int,
    arg(help='Fallback max. line length for darker/isort etc., if not defined in .editorconfig'),
]
DarkerPrefixesType = Annotated[
    str,
    arg(help='Apply prefixes via autopep8 before calling darker.'),
]
RemoveAllUnusedImportsType = Annotated[
    bool,
    arg(help='Remove all unused imports (not just those from the standard library) via autoflake'),
]


@cli.register
def format_file(
    file_path: Annotated[Path, arg(help='The python source code file to format.')],
    /,
    py_version: PyVersionType = FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION,
    max_line_length: MaxLineLengthType = FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
    darker_prefixes: DarkerPrefixesType = FORMAT_PY_FILE_DARKER_PRE_FIXES,
    remove_all_unused_imports: RemoveAllUnusedImportsType = True,
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
        remove_all_unused_imports=remove_all_unused_imports,
        file_path=file_path,
    )


@cli.register
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)
