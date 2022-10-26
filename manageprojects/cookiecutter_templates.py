import dataclasses
import datetime
import logging
from pathlib import Path

import tomli
import tomlkit
from cookiecutter.config import get_user_config
from cookiecutter.main import cookiecutter
from cookiecutter.repository import determine_repo_dir

from manageprojects.git import Git
from manageprojects.path_utils import assert_is_dir, assert_is_file


logger = logging.getLogger(__name__)

INITIAL_REVISION = 'initial_revision'
INITIAL_DATE = 'initial_date'
APPLIED_MIGRATIONS = 'applied_migrations'


@dataclasses.dataclass
class CookiecutterResult:
    """
    Store information about a created Cookiecutter template
    """

    destination_path: Path = None
    git_path: Path = None
    git_hash: str = None
    commit_date: datetime.datetime = None
    pyproject_toml_path: Path = None

    def get_comment(self):
        if self.commit_date:
            return self.commit_date.isoformat()
        return ''


@dataclasses.dataclass
class ManageProjectsMeta:
    """
    Information about 'manageprojects' git hashes
    """

    initial_revision: str = None
    initial_date: datetime.datetime = None
    applied_migrations: list[str] = None


def parse_pyproject_toml(path: Path) -> ManageProjectsMeta:
    """
    Load 'manageprojects' information from 'pyproject.toml' file.
    """
    assert_is_file(path)
    toml_dict = tomli.loads(path.read_text(encoding='UTF-8'))

    result = ManageProjectsMeta(applied_migrations=[])
    if data := toml_dict.get('manageprojects'):
        result.initial_revision = data.get(INITIAL_REVISION)
        if raw_date := data.get(INITIAL_DATE):
            try:
                result.initial_date = datetime.datetime.fromisoformat(raw_date)
            except ValueError as err:
                logger.warning(f'Can not parse initial date: {err}')
        if applied_migrations := data.get(APPLIED_MIGRATIONS):
            result.applied_migrations = applied_migrations
    return result


def get_last_git_hash(path: Path) -> str:
    """
    Get the lash git hash from 'pyproject.toml' file.
    """
    if meta := parse_pyproject_toml(path):
        if migrations := meta.applied_migrations:
            return migrations[-1]
        return meta.initial_revision


def update_pyproject_toml(result: CookiecutterResult) -> Path:
    """
    Store git hash/migration information into 'pyproject.toml' in destination path.
    """
    pyproject_toml_path = result.destination_path / 'pyproject.toml'
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
        manageprojects = doc['manageprojects']

        if 'applied_migrations' not in manageprojects:
            applied_migrations = tomlkit.array()
            applied_migrations.multiline(multiline=True)
            manageprojects.add(APPLIED_MIGRATIONS, applied_migrations)
        else:
            applied_migrations = manageprojects[APPLIED_MIGRATIONS]
        applied_migrations.add_line(result.git_hash, comment=result.get_comment())

    pyproject_toml_path.write_text(tomlkit.dumps(doc), encoding='UTF-8')
    return pyproject_toml_path


def run_cookiecutter(
    *,
    template: str,
    checkout: str = None,
    password: str = None,
    directory: str = None,
    config_file: Path = None,
    **cookiecutter_kwargs,
) -> CookiecutterResult:
    config_dict = get_user_config(
        config_file=config_file,
        default_config=None,
    )
    repo_dir, cleanup = determine_repo_dir(
        template=template,
        abbreviations=config_dict['abbreviations'],
        clone_to_dir=config_dict['cookiecutters_dir'],
        checkout=checkout,
        no_input=True,
        password=password,
        directory=directory,
    )
    logger.debug('repo_dir: %s', repo_dir)

    cookiecutter_kwargs.update(
        dict(
            template=template,
            checkout=checkout,
            password=password,
            directory=directory,
            config_file=config_file,
        )
    )
    logger.debug('Call cookiecutter with: %r', cookiecutter_kwargs)
    destination = cookiecutter(**cookiecutter_kwargs)
    destination_path = Path(destination)
    assert_is_dir(destination_path)
    logger.info('Cookiecutter generated here: %r', destination_path)

    repo_path = Path(repo_dir)
    assert_is_dir(repo_path)
    git = Git(cwd=repo_path)
    logger.debug('Cookiecutter git repro: %s', git.cwd)
    current_hash = git.get_current_hash()
    commit_date = git.get_commit_date()
    logger.info('Cookiecutter git repro: %s hash: %r %s', git.cwd, current_hash, commit_date)

    result = CookiecutterResult(
        destination_path=destination_path,
        git_path=git.cwd,
        git_hash=current_hash,
        commit_date=commit_date,
    )

    pyproject_toml_path = update_pyproject_toml(result)
    result.pyproject_toml_path = pyproject_toml_path

    return result
