import datetime
import logging
from pathlib import Path
from typing import Optional

import tomlkit
from bx_py_utils.path import assert_is_dir

from manageprojects.constants import (
    APPLIED_MIGRATIONS,
    COOKIECUTTER_CONTEXT,
    COOKIECUTTER_DIRECTORY,
    COOKIECUTTER_TEMPLATE,
    INITIAL_DATE,
    INITIAL_REVISION,
)
from manageprojects.data_classes import ManageProjectsMeta


logger = logging.getLogger(__name__)


class PyProjectToml:
    """
    Helper for manageprojects meta information in 'pyproject.toml'
    """

    def __init__(self, project_path: Path):
        assert_is_dir(project_path)
        self.path = project_path / 'pyproject.toml'

        if self.path.exists():
            logger.debug('Read existing pyproject.toml')
            self.doc = tomlkit.parse(self.path.read_text(encoding='UTF-8'))
        else:
            logger.debug('Create new pyproject.toml')
            self.doc = tomlkit.document()
            self.doc.add(tomlkit.comment('Created by manageprojects'))

        if 'manageprojects' in self.doc:
            self.mp_table = self.doc['manageprojects']
        else:
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
        self.mp_table.add(INITIAL_REVISION, revision)
        self.mp_table.add(INITIAL_DATE, dt)
        self.mp_table.add(COOKIECUTTER_TEMPLATE, template)
        if directory:
            self.mp_table.add(COOKIECUTTER_DIRECTORY, directory)

    def create_or_update_cookiecutter_context(self, context: dict) -> None:
        if COOKIECUTTER_CONTEXT in self.mp_table:
            context_table = self.mp_table[COOKIECUTTER_CONTEXT]
        else:
            context_table = tomlkit.table(is_super_table=False)

        filtered_dict = {key: value for key, value in context.items() if not key.startswith('_')}
        context_table.update(filtered_dict)
        if COOKIECUTTER_CONTEXT not in self.mp_table:
            self.mp_table.append(COOKIECUTTER_CONTEXT, context_table)

    def add_applied_migrations(self, git_hash: str, dt: datetime.datetime) -> None:
        if APPLIED_MIGRATIONS not in self.mp_table:
            applied_migrations = tomlkit.array()
            applied_migrations.multiline(multiline=True)
            self.mp_table.add(APPLIED_MIGRATIONS, applied_migrations)
        else:
            applied_migrations = self.mp_table[APPLIED_MIGRATIONS]
        applied_migrations.add_line(git_hash, comment=dt.isoformat())

    ###############################################################################################

    def dumps(self) -> str:
        return self.doc.as_string()

    def save(self) -> None:
        content = self.dumps()
        self.path.write_text(content, encoding='UTF-8')

    ###############################################################################################

    def get_mp_meta(self) -> ManageProjectsMeta:
        kwargs = dict(
            initial_revision=self.mp_table.get(INITIAL_REVISION),
            initial_date=self.mp_table.get(INITIAL_DATE),
            applied_migrations=self.mp_table.get(APPLIED_MIGRATIONS, []),
            cookiecutter_template=self.mp_table.get(COOKIECUTTER_TEMPLATE),
            cookiecutter_directory=self.mp_table.get(COOKIECUTTER_DIRECTORY),
            cookiecutter_context=self.mp_table.get(COOKIECUTTER_CONTEXT),
        )
        logger.debug('Create ManageProjectsMeta with: %r', kwargs)
        result = ManageProjectsMeta(**kwargs)
        return result
