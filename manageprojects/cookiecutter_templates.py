import logging
from pathlib import Path

from bx_py_utils.path import assert_is_dir
from cookiecutter.config import get_user_config
from cookiecutter.main import cookiecutter
from cookiecutter.repository import determine_repo_dir

from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.git import Git
from manageprojects.patching import generate_template_patch
from manageprojects.utilities.pyproject_toml import parse_pyproject_toml, update_pyproject_toml


logger = logging.getLogger(__name__)


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

    pyproject_toml_path = destination_path / 'pyproject.toml'

    result = CookiecutterResult(
        destination_path=destination_path,
        git_path=git.cwd,
        git_hash=current_hash,
        commit_date=commit_date,
        pyproject_toml_path=pyproject_toml_path,
    )
    update_pyproject_toml(result)
    return result


def update_project(project_path: Path):
    pyproject_toml_path = project_path / 'pyproject.toml'

    meta: ManageProjectsMeta = parse_pyproject_toml(pyproject_toml_path)

    generate_template_patch(meta)
