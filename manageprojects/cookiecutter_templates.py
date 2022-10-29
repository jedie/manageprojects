import logging
from pathlib import Path
from typing import Optional
from unittest.mock import patch

from bx_py_utils.path import assert_is_dir
from cookiecutter import generate
from cookiecutter.config import get_user_config
from cookiecutter.main import cookiecutter
from cookiecutter.repository import determine_repo_dir

from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.git import Git
from manageprojects.patching import GenerateTemplatePatchResult, generate_template_patch
from manageprojects.utilities.pyproject_toml import PyProjectToml


logger = logging.getLogger(__name__)


class CookieCutterHookHandler:
    """
    Capture the effective Cookiecutter Template Context via injecting the Cookiecutter hooks.
    """

    def __init__(self, origin_run_hook):
        self.origin_run_hook = origin_run_hook
        self.context = {}

    def __call__(self, hook_name, project_dir, context):
        logger.debug('Hook %r for %r context: %r', hook_name, project_dir, context)
        origin_hook_result = self.origin_run_hook(hook_name, project_dir, context)
        self.context.update(context)
        return origin_hook_result


def get_repo_path(
    *,
    template: str,  # CookieCutter Template path or GitHub url
    directory: str = None,  # Directory name of the CookieCutter Template
    checkout: str = None,
    password: str = None,
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
) -> Path:
    if directory:
        assert '://' not in directory
        assert template != directory

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

    repo_path = Path(repo_dir)
    assert_is_dir(repo_path)
    return repo_path


def run_cookiecutter(
    *,
    template: str,  # CookieCutter Template path or GitHub url
    output_dir: Path,  # Target path where CookieCutter should store the result files
    directory: str = None,  # Directory name of the CookieCutter Template
    checkout: str = None,
    password: str = None,
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
    **cookiecutter_kwargs,
) -> CookiecutterResult:

    repo_path = get_repo_path(
        template=template,
        directory=directory,
        checkout=checkout,
        password=password,
        config_file=config_file,
    )

    cookiecutter_kwargs.update(
        dict(
            template=template,
            output_dir=output_dir,
            directory=directory,
            checkout=checkout,
            password=password,
            config_file=config_file,
        )
    )
    logger.debug('Call cookiecutter with: %r', cookiecutter_kwargs)

    run_hook = CookieCutterHookHandler(origin_run_hook=generate.run_hook)
    with patch.object(generate, 'run_hook', run_hook):
        destination = cookiecutter(**cookiecutter_kwargs)
    complete_context = run_hook.context
    logger.info('Complete used context: %r', complete_context)
    cookiecutter_context = complete_context['cookiecutter']
    logger.info('Used cookiecutter context: %r', cookiecutter_context)

    destination_path = Path(destination)
    assert_is_dir(destination_path)
    logger.info('Cookiecutter generated here: %r', destination_path)

    git = Git(cwd=repo_path)
    logger.debug('Cookiecutter git repro: %s', git.cwd)
    current_hash = git.get_current_hash()
    commit_date = git.get_commit_date()
    logger.info('Cookiecutter git repro: %s hash: %r %s', git.cwd, current_hash, commit_date)

    # Create or update "pyproject.toml" with manageprojects information:
    toml = PyProjectToml(project_path=destination_path)
    toml.init(
        revision=current_hash,
        dt=commit_date,
        template=template,
        directory=directory,
    )
    toml.create_or_update_cookiecutter_context(context=cookiecutter_context)
    toml.save()

    result = CookiecutterResult(
        destination_path=destination_path,
        git_path=git.cwd,
        git_hash=current_hash,
        commit_date=commit_date,
        cookiecutter_context=cookiecutter_context,
    )
    return result


def update_project(
    project_path: Path,
    password: str = None,
    config_file: Optional[Path] = None,  # CookieCutter config file
) -> Optional[GenerateTemplatePatchResult]:
    print(f'Update project: {project_path}', end=' ')
    git = Git(cwd=project_path, detect_root=True)

    toml = PyProjectToml(project_path=project_path)
    meta: ManageProjectsMeta = toml.get_mp_meta()

    from_rev = meta.get_last_git_hash()
    assert from_rev, f'Fail to get last gut hash from {toml.path}'

    cookiecutter_context = meta.cookiecutter_context
    assert cookiecutter_context, f'Missing cookiecutter context in {toml.path}'

    cookiecutter_template = meta.cookiecutter_template
    assert cookiecutter_template, f'Missing template in {toml.path}'

    repo_path = get_repo_path(
        template=cookiecutter_template,
        directory=meta.cookiecutter_directory,
        checkout=None,
        password=password,
        config_file=config_file,
    )

    result = generate_template_patch(
        project_path=project_path,
        repo_path=repo_path,
        from_rev=from_rev,
        replay_context=cookiecutter_context,
    )
    if not result:
        # Nothing to apply
        return None
    assert isinstance(result, GenerateTemplatePatchResult)

    patch_file_path = result.patch_file_path
    git.apply(patch_path=patch_file_path)

    # Update "pyproject.toml" with applied patch information:
    toml.add_applied_migrations(git_hash=result.to_rev, dt=result.commit_date)
    toml.save()

    return result
