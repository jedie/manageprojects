import logging
import shutil
from pathlib import Path
from typing import Optional

from bx_py_utils.path import assert_is_dir
from rich import print

from manageprojects.cookiecutter_api import execute_cookiecutter
from manageprojects.data_classes import GenerateTemplatePatchResult
from manageprojects.git import Git
from manageprojects.utilities.temp_path import TemporaryDirectory


logger = logging.getLogger(__name__)


def verbose_copy(src, dst):
    logger.info(f'copy: "{src}" to "{dst}"')
    shutil.copy2(src, dst)


def make_git_diff(temp_path: Path, from_path: Path, to_path: Path, verbose=True) -> Optional[str]:
    """
    Create git diff between from_path and to_path
    """
    print(f'Make git diff between {from_path} and {to_path} (temp: {temp_path})')
    assert_is_dir(from_path)
    assert_is_dir(to_path)

    temp_repo_path = temp_path / 'git-repo'

    # Create git repo with "from" content:
    shutil.copytree(
        src=from_path,
        dst=temp_repo_path,
        ignore=shutil.ignore_patterns('.git'),
        copy_function=verbose_copy,
        dirs_exist_ok=False,
    )
    assert not Path(temp_repo_path, '.git').exists()
    git = Git(cwd=temp_repo_path, detect_root=False)
    git.init(verbose=verbose)
    git.add('.', verbose=False)
    git.commit('init with "from" revision', verbose=False)
    git.print_file_list(out_func=logger.info)

    # Remove all files, except .git:
    for item in temp_repo_path.iterdir():
        if item.is_dir():
            if item.name == '.git':
                continue
            shutil.rmtree(item)
        else:
            item.unlink()

    # Commit "to" version:
    shutil.copytree(
        src=to_path,
        dst=temp_repo_path,
        ignore=shutil.ignore_patterns('.git'),
        copy_function=verbose_copy,
        dirs_exist_ok=True,
    )
    git.add('.', verbose=verbose)
    git.commit('Commit "to" revision', verbose=verbose)
    git.print_file_list(out_func=logger.info)

    # Diff between previous commit (from) and current commit (to):
    patch = git.diff('HEAD^', 'HEAD')
    if not patch:
        logger.warning(f'No gif diff between {from_path} and {to_path} !')
        return None

    return patch


def generate_template_patch(
    *,
    project_path: Path,
    template: str,  # CookieCutter Template path or GitHub url
    from_rev: str,
    replay_context: dict,
    directory: Optional[str] = None,  # Directory name of the CookieCutter Template
    password: Optional[str] = None,
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
    cleanup: bool = True,  # Remove temp files if not exceptions happens
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
) -> Optional[GenerateTemplatePatchResult]:
    """
    Create git diff/patch from cookiecutter template changes.
    """
    print(f'Generate update patch for project: {project_path} from {template}')
    project_name = project_path.name

    extra_context = replay_context.get('cookiecutter')
    if not extra_context:
        print('WARNING: No "cookiecutter" in replay context!')

    with TemporaryDirectory(prefix=f'manageprojects_{project_name}_', cleanup=cleanup) as temp_path:

        #############################################################################
        # Generate the cookiecutter template in the current/HEAD version:

        compiled_to_path = temp_path / 'to_rev_compiled'
        print(f'Compile cookiecutter template in the current version here: {compiled_to_path}')
        print('Use extra context:')
        print(extra_context)
        to_rev_context, to_rev_dst_path, to_rev_repo_path = execute_cookiecutter(
            template=template,
            directory=directory,
            output_dir=compiled_to_path,
            no_input=no_input,
            extra_context=extra_context,
            checkout=None,  # Checkout HEAD/main revision
            password=password,
            config_file=config_file,
        )

        assert_is_dir(to_rev_repo_path)
        assert to_rev_dst_path.parent == compiled_to_path

        #############################################################################
        # Get the current git commit hash and date:

        git = Git(cwd=to_rev_repo_path, detect_root=True)
        to_rev = git.get_current_hash(verbose=False)
        to_commit_date = git.get_commit_date(verbose=False)
        print(f'Update from rev. {from_rev} to rev. {to_rev} ({to_commit_date})')

        if from_rev == to_rev:
            print(
                f'Latest version {from_rev!r}'
                f' from {to_commit_date} is already applied.'
                ' Nothing to update, ok.'
            )
            return None

        if 'github.com' in template:
            print(f'Github compare: {template}/compare/{from_rev}...{to_rev}')

        patch_file_path = Path(
            project_path, '.manageprojects', 'patches', f'{from_rev}_{to_rev}.patch'
        )
        print(f'Generate patch file: {patch_file_path}')

        #############################################################################
        # Generate the cookiecutter template in the old version:

        compiled_from_path = temp_path / f'{from_rev}_compiled'
        print(
            'Compile cookiecutter template in the'
            f' old {from_rev} version here: {compiled_from_path}'
        )
        print('Use extra context:')
        print(extra_context)
        from_rev_context, from_rev_dst_path, from_repo_path = execute_cookiecutter(
            template=template,
            directory=directory,
            output_dir=compiled_from_path,
            no_input=no_input,
            extra_context=extra_context,
            checkout=from_rev,  # Checkout the old revision
            password=password,
            config_file=config_file,
        )
        assert_is_dir(from_repo_path)
        assert from_repo_path == to_rev_repo_path
        assert from_rev_dst_path.parent == compiled_from_path

        #############################################################################
        # Generate git patch between old and current version:

        patch = make_git_diff(
            temp_path=temp_path,
            from_path=from_rev_dst_path,
            to_path=to_rev_dst_path,
            verbose=False,
        )
        if not patch:
            print(f'No gif diff between {compiled_from_path} and {compiled_to_path} !')
            return None

        logger.info('Write patch file: %s', patch_file_path)
        patch_file_path.parent.mkdir(parents=True, exist_ok=True)
        patch_file_path.write_text(patch)

        return GenerateTemplatePatchResult(
            repo_path=to_rev_repo_path,  # == from_repo_path
            patch_file_path=patch_file_path,
            from_rev=from_rev,
            compiled_from_path=compiled_from_path,
            to_rev=to_rev,
            to_commit_date=to_commit_date,
            compiled_to_path=compiled_to_path,
        )
