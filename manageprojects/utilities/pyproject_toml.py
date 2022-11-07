import datetime
import logging
from pathlib import Path
from typing import Optional

import tomlkit
from bx_py_utils.path import assert_is_dir, assert_is_file
from tomlkit import TOMLDocument
from tomlkit.items import Table

from manageprojects.constants import (
    APPLIED_MIGRATIONS,
    COOKIECUTTER_CONTEXT,
    COOKIECUTTER_DIRECTORY,
    COOKIECUTTER_TEMPLATE,
    INITIAL_DATE,
    INITIAL_REVISION,
)
from manageprojects.data_classes import ManageProjectsMeta
from manageprojects.utilities.log_utils import log_func_call


logger = logging.getLogger(__name__)


def toml_load(path: Path) -> dict:
    assert_is_file(path)
    doc: TOMLDocument = tomlkit.parse(path.read_text(encoding='UTF-8'))
    return dict(doc)


class PyProjectToml:
    """
    Helper for manageprojects meta information in 'pyproject.toml'
    """

    def __init__(self, project_path: Path):
        assert_is_dir(project_path)
        self.path = project_path / 'pyproject.toml'

        if self.path.exists():
            logger.debug('Read existing pyproject.toml')
            self.doc: TOMLDocument = tomlkit.parse(self.path.read_text(encoding='UTF-8'))
        else:
            logger.debug('Create new pyproject.toml')
            self.doc: TOMLDocument = tomlkit.document()  # type: ignore
            self.doc.add(tomlkit.comment('Created by manageprojects'))

        self.mp_table: Table = self.doc.get('manageprojects')  # type: ignore
        if not self.mp_table:
            # Insert: [manageprojects]
            if self.path.exists():
                self.doc.add(tomlkit.ws('\n\n'))  # Add a new empty line
            self.mp_table = tomlkit.table()
            self.mp_table.comment('https://github.com/jedie/manageprojects')
            self.doc.append('manageprojects', self.mp_table)

    def init(
        self, revision, dt: datetime.datetime, template: str, directory: Optional[str]
    ) -> None:
        assert INITIAL_REVISION not in self.mp_table
        assert INITIAL_DATE not in self.mp_table
        assert COOKIECUTTER_TEMPLATE not in self.mp_table
        self.mp_table.add(INITIAL_REVISION, revision)
        self.mp_table.add(INITIAL_DATE, dt)
        self.mp_table.add(COOKIECUTTER_TEMPLATE, template)
        if directory:
            self.mp_table.add(COOKIECUTTER_DIRECTORY, directory)

    def create_or_update_cookiecutter_context(self, context: dict) -> None:
        # Don't store the '_output_dir':
        context['cookiecutter'] = {
            k: v for k, v in context['cookiecutter'].items() if k != '_output_dir'
        }
        self.mp_table[COOKIECUTTER_CONTEXT] = tomlkit.item(context)

    def add_applied_migrations(self, git_hash: str, dt: datetime.datetime) -> None:
        if not (applied_migrations := self.mp_table.get(APPLIED_MIGRATIONS)):
            # Add: applied_migrations = []
            applied_migrations = tomlkit.array()
            applied_migrations.multiline(multiline=True)
            self.mp_table.add(APPLIED_MIGRATIONS, applied_migrations)

        # Append git_hash to applied_migrations:
        applied_migrations.add_line(git_hash, comment=dt.isoformat())

    ###############################################################################################

    def dumps(self) -> str:
        return self.doc.as_string()

    def save(self) -> None:
        content = self.dumps()
        self.path.write_text(content, encoding='UTF-8')

    ###############################################################################################

    def get_mp_meta(self) -> ManageProjectsMeta:
        data = self.mp_table.unwrap()  # change tomlkit.Container to a normal dict
        result: ManageProjectsMeta = log_func_call(
            logger=logger,
            func=ManageProjectsMeta,
            initial_revision=data.get(INITIAL_REVISION),
            initial_date=data.get(INITIAL_DATE),
            applied_migrations=data.get(APPLIED_MIGRATIONS, []),
            cookiecutter_template=data.get(COOKIECUTTER_TEMPLATE),
            cookiecutter_directory=data.get(COOKIECUTTER_DIRECTORY),
            cookiecutter_context=data.get(COOKIECUTTER_CONTEXT),
        )
        return result
