import datetime
import logging
from pathlib import Path

import tomli
import tomlkit
from bx_py_utils.path import assert_is_file

from manageprojects.constants import APPLIED_MIGRATIONS, INITIAL_DATE, INITIAL_REVISION
from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.exceptions import NoManageprojectsMeta, ProjectNotFound


logger = logging.getLogger(__name__)


def parse_pyproject_toml(path: Path) -> ManageProjectsMeta:
    """
    Load 'manageprojects' information from 'pyproject.toml' file.
    """
    try:
        assert_is_file(path)
    except (NotADirectoryError, FileNotFoundError) as err:
        raise ProjectNotFound(f'Project not found here: {path.parent} - Error: {err}')

    toml_dict = tomli.loads(path.read_text(encoding='UTF-8'))
    data = toml_dict.get('manageprojects')
    if not data:
        logger.warning(f'pyproject {path} does not contain [manageprojects] information')
        raise NoManageprojectsMeta()

    initial_date = None
    if raw_date := data.get(INITIAL_DATE):
        try:
            initial_date = datetime.datetime.fromisoformat(raw_date)
        except ValueError as err:
            logger.warning(f'Can not parse initial date: {err}')

    result = ManageProjectsMeta(
        initial_revision=data.get(INITIAL_REVISION),
        applied_migrations=data.get(APPLIED_MIGRATIONS, []),
        initial_date=initial_date,
    )
    return result


def update_pyproject_toml(result: CookiecutterResult) -> None:
    """
    Store git hash/migration information into 'pyproject.toml' in destination path.
    """
    pyproject_toml_path = result.pyproject_toml_path
    if pyproject_toml_path.exists():
        doc = tomlkit.parse(pyproject_toml_path.read_text(encoding='UTF-8'))
    else:
        doc = tomlkit.document()
        doc.add(tomlkit.comment('Created by manageprojects'))

    if 'manageprojects' not in doc:
        manageprojects = tomlkit.table()
        manageprojects.comment('https://github.com/jedie/manageprojects')
        manageprojects.add(INITIAL_REVISION, result.git_hash)
        if result.commit_date:
            manageprojects.add(INITIAL_DATE, result.get_comment())
        doc['manageprojects'] = manageprojects
    else:
        manageprojects = doc['manageprojects']  # type: ignore

        if 'applied_migrations' not in manageprojects:
            applied_migrations = tomlkit.array()
            applied_migrations.multiline(multiline=True)
            manageprojects.add(APPLIED_MIGRATIONS, applied_migrations)
        else:
            applied_migrations = manageprojects[APPLIED_MIGRATIONS]  # type: ignore
        applied_migrations.add_line(result.git_hash, comment=result.get_comment())

    pyproject_toml_path.write_text(tomlkit.dumps(doc), encoding='UTF-8')
