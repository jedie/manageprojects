import dataclasses
import datetime
import logging
from pathlib import Path

import tomlkit
from bx_py_utils.path import assert_is_dir, assert_is_file
from cli_base.cli_tools.rich_utils import human_error
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
from manageprojects.exceptions import NoPyProjectTomlFound
from manageprojects.utilities.log_utils import log_func_call


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TomlDocument:
    file_path: Path
    doc: TOMLDocument


def get_toml_document(path: Path) -> TomlDocument:
    """
    Read the file path and returns the TOMLDocument.
    Just use unwrap() if a normal dict is needed, e.g.:

        doc: TOMLDocument = get_toml_document(path)
        toml: dict = doc.unwrap()
    """
    assert_is_file(path)
    doc: TOMLDocument = tomlkit.parse(path.read_text(encoding='UTF-8'))

    return TomlDocument(file_path=path, doc=doc)


def find_pyproject_toml(file_path: Path) -> Path | None:
    """
    Go back down the directory tree to find the "pyproject.toml" file.
    """
    if file_path.is_file():
        return find_pyproject_toml(file_path.parent)

    pyproject_toml = file_path / 'pyproject.toml'
    if pyproject_toml.is_file():
        return pyproject_toml

    if parent_path := file_path.parent:
        if parent_path != file_path:
            return find_pyproject_toml(parent_path)

    return None


def get_pyproject_toml(*, file_path: Path | None = None) -> TomlDocument:
    """
    Find the "pyproject.toml" and return it.
    """
    if not file_path:
        file_path = Path.cwd()
    pyproject_toml_path = find_pyproject_toml(file_path=file_path)
    if not pyproject_toml_path:
        raise NoPyProjectTomlFound(f'Can not find "pyproject.toml" in {file_path}')

    assert_is_file(pyproject_toml_path)
    toml_document: TomlDocument = get_toml_document(pyproject_toml_path)
    return toml_document


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

    def init(self, revision, dt: datetime.datetime, template: str, directory: str | None) -> None:
        assert INITIAL_REVISION not in self.mp_table
        assert INITIAL_DATE not in self.mp_table
        assert COOKIECUTTER_TEMPLATE not in self.mp_table
        self.mp_table.add(INITIAL_REVISION, revision)
        self.mp_table.add(INITIAL_DATE, dt)
        self.mp_table.add(COOKIECUTTER_TEMPLATE, template)
        if directory:
            self.mp_table.add(COOKIECUTTER_DIRECTORY, directory)

    def create_or_update_cookiecutter_context(self, context: dict) -> None:
        cc_context = context['cookiecutter']
        excluded_keys = {'_output_dir', '_repo_dir', '_checkout'}
        cc_context = {k: v for k, v in cc_context.items() if k not in excluded_keys}
        context = {'cookiecutter': cc_context}
        try:
            self.mp_table[COOKIECUTTER_CONTEXT] = tomlkit.item(context)
        except (TypeError, ValueError) as err:
            human_error(message=f'Unable to load {context=}', exception=err, exit_code=-1)

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


def update_pyproject_toml(*, old_mp_table: Table, project_path, git_hash: str, dt: datetime.datetime) -> None:
    # Important: We *must* read the current "pyproject.toml" here again!
    # Otherwise, we may overwrite template changed with old content!
    toml = PyProjectToml(project_path=project_path)

    if not (applied_migrations := old_mp_table.get(APPLIED_MIGRATIONS)):
        # Add: applied_migrations = []
        applied_migrations = tomlkit.array()
        applied_migrations.multiline(multiline=True)
        old_mp_table.add(APPLIED_MIGRATIONS, applied_migrations)

    # Append git_hash to applied_migrations:
    applied_migrations.add_line(git_hash, comment=dt.isoformat())

    # "Overwrite" the old manageprojects table with the new one:
    toml.doc['manageprojects'] = old_mp_table

    toml.save()
