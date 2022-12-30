import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich import print as rprint

from manageprojects.cookiecutter_api import execute_cookiecutter
from manageprojects.data_classes import (
    CookiecutterResult,
    GenerateTemplatePatchResult,
    ManageProjectsMeta,
)
from manageprojects.git import Git
from manageprojects.patching import generate_template_patch
from manageprojects.utilities.pyproject_toml import PyProjectToml


logger = logging.getLogger(__name__)


def start_managed_project(
    *,
    template: str,  # CookieCutter Template path or GitHub url
    output_dir: Path,  # Target path where CookieCutter should store the result files
    directory: Optional[str] = None,  # Directory name of the CookieCutter Template
    no_input: bool = False,
    extra_context: Optional[dict] = None,
    replay: Optional[bool] = None,
    checkout: Optional[str] = None,
    password: Optional[str] = None,  # Optional password to use when extracting the repository
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
) -> CookiecutterResult:
    """
    Start a new "managed" project by run cookiecutter and create/update "pyproject.toml"
    """

    #############################################################################
    # Run cookiecutter

    cookiecutter_context, destination_path, repo_path = execute_cookiecutter(
        template=template,
        directory=directory,
        output_dir=output_dir,
        no_input=no_input,
        extra_context=extra_context,
        replay=replay,
        checkout=checkout,
        password=password,
        config_file=config_file,
    )

    git = Git(cwd=repo_path)
    logger.debug('Cookiecutter git repro: %s', git.cwd)
    current_hash = git.get_current_hash()
    commit_date = git.get_commit_date()
    logger.info('Cookiecutter git repro: %s hash: %r %s', git.cwd, current_hash, commit_date)

    #############################################################################
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


def update_managed_project(
    project_path: Path,
    password: Optional[str] = None,
    config_file: Optional[Path] = None,  # CookieCutter config file
    cleanup: bool = True,  # Remove temp files if not exceptions happens
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
) -> Optional[GenerateTemplatePatchResult]:
    """
    Update a existing project by apply git patch from cookiecutter template changes.
    """
    print(f'Update project: {project_path}', end=' ')
    git = Git(cwd=project_path, detect_root=True)

    #############################################################################
    # Get information from project's pyproject.toml

    toml = PyProjectToml(project_path=project_path)
    meta: ManageProjectsMeta = toml.get_mp_meta()

    from_rev = meta.get_last_git_hash()
    assert from_rev, f'Fail to get last git hash from {toml.path}'

    cookiecutter_context = meta.cookiecutter_context
    assert cookiecutter_context, f'Missing cookiecutter context in {toml.path}'

    cookiecutter_template = meta.cookiecutter_template
    assert cookiecutter_template, f'Missing template in {toml.path}'

    #############################################################################
    # Generate the git diff/patch

    result = generate_template_patch(
        project_path=project_path,
        template=cookiecutter_template,
        directory=meta.cookiecutter_directory,
        from_rev=from_rev,
        replay_context=cookiecutter_context,
        password=password,
        config_file=config_file,
        cleanup=cleanup,
        no_input=no_input,
    )
    if not result:
        logger.info('No git patch was created, nothing to apply.')
        return None
    assert isinstance(result, GenerateTemplatePatchResult)

    #############################################################################
    # Apply the patch

    patch_file_path = result.patch_file_path
    try:
        git.apply(patch_path=patch_file_path)
    except subprocess.CalledProcessError as err:
        print(err.stdout)
        if err.returncode == 1:
            print()
            print('Seems that the patch was not applied correctly!')
            print('Hint: run wiggle on the project:')
            print()
            print(f'./cli.py wiggle {project_path}')
            print()

    #############################################################################
    # Update "pyproject.toml" with applied patch information

    # Important: We *must* read the current "pyproject.toml" here again!
    # Otherwise we may overwrite template changed with old content!
    toml = PyProjectToml(project_path=project_path)
    toml.add_applied_migrations(git_hash=result.to_rev, dt=result.to_commit_date)
    toml.save()

    return result


def clone_managed_project(
    project_path: Path,
    destination: Path,
    checkout: Optional[str] = None,  # Optional branch, tag or commit ID to checkout after clone
    password: Optional[str] = None,
    config_file: Optional[Path] = None,  # CookieCutter config file
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
) -> CookiecutterResult:
    """
    Clone a existing project by replay the cookiecutter template in a new directory.
    """
    rprint(f'Clone {project_path} to {destination}')
    if destination.exists():
        print(f'ERROR: Destination {destination} already exists!')
        sys.exit(1)

    toml = PyProjectToml(project_path=project_path)
    meta: ManageProjectsMeta = toml.get_mp_meta()

    cookiecutter_context = meta.cookiecutter_context
    assert cookiecutter_context, f'Missing cookiecutter context in {toml.path}'

    extra_context = cookiecutter_context.get('cookiecutter')
    if not extra_context:
        print('WARNING: No "cookiecutter" in replay context!')

    cookiecutter_template = meta.cookiecutter_template
    assert cookiecutter_template, f'Missing template in {toml.path}'

    cookiecutter_directory = meta.cookiecutter_directory

    print('Use extra context:')
    rprint(extra_context)
    new_context, destination_path, repo_path = execute_cookiecutter(
        template=cookiecutter_template,
        directory=cookiecutter_directory,
        output_dir=destination,
        no_input=no_input,
        extra_context=extra_context,
        checkout=checkout,
        password=password,
        config_file=config_file,
    )

    git = Git(cwd=repo_path)
    logger.debug('Cookiecutter git repro: %s', git.cwd)
    current_hash = git.get_current_hash()
    commit_date = git.get_commit_date()
    logger.info('Cookiecutter git repro: %s hash: %r %s', git.cwd, current_hash, commit_date)

    #############################################################################
    # Create "pyproject.toml" with manageprojects information:

    toml = PyProjectToml(project_path=destination_path)
    toml.init(
        revision=current_hash,
        dt=commit_date,
        template=cookiecutter_template,
        directory=cookiecutter_directory,
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
    print(f'{project_path} successfully cloned to {destination_path}')
    return result
