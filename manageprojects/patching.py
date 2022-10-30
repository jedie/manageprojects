import dataclasses
import datetime
import logging
import shutil
from pathlib import Path
from typing import Optional

from cookiecutter.generate import generate_files
from rich import print  # noqa

from manageprojects.git import Git
from manageprojects.utilities.temp_path import TemporaryDirectory
from manageprojects.utilities.user_config import get_patch_path


logger = logging.getLogger(__name__)


def cp_git_rev(git: Git, rev: str, dst: Path):
    git.git_verbose_check_call('reset', '--hard', rev)
    shutil.copytree(src=git.cwd, dst=dst)


@dataclasses.dataclass
class GenerateTemplatePatchResult:
    patch_file_path: Path
    to_rev: str
    commit_date: datetime.datetime


def generate_template_patch(
    project_path: Path, repo_path: Path, from_rev: str, replay_context: dict
) -> Optional[GenerateTemplatePatchResult]:
    print(f'Generate update patch for project: {project_path} from {repo_path}')

    git = Git(cwd=repo_path, detect_root=True)
    git.git_verbose_check_call('fetch')
    to_rev = git.get_current_hash(verbose=False)
    commit_date = git.get_commit_date(verbose=False)
    print(f'Update from rev. {from_rev} to rev. {to_rev} ({commit_date})')

    if from_rev == to_rev:
        commit_date = git.get_commit_date()
        print(
            f'Latest version {from_rev!r}'
            f' from {commit_date} is already applied.'
            ' Nothing to update, ok.'
        )
        return None

    project_name = project_path.name

    patch_path = get_patch_path()
    patch_file_path = patch_path / f'{project_name}_{from_rev}_{to_rev}.patch'
    print(f'Generate patch file: {patch_file_path}')

    with TemporaryDirectory(prefix=f'manageprojects_{project_name}_') as temp_path:

        template_name = repo_path.name
        from_rev_path = temp_path / from_rev / template_name
        to_rev_path = temp_path / to_rev / template_name

        git.git_verbose_check_call('reset', '--hard', from_rev)
        shutil.copytree(src=git.cwd, dst=from_rev_path)

        git.git_verbose_check_call('reset', '--hard', to_rev)
        shutil.copytree(src=git.cwd, dst=to_rev_path)

        compiled_from_path = temp_path / f'{from_rev}_compiled'
        kwargs = dict(
            repo_dir=from_rev_path,
            context=replay_context,
            overwrite_if_exists=False,
            skip_if_file_exists=False,
            output_dir=compiled_from_path,
        )
        logger.debug('Generate files with: %r', kwargs)
        generate_files(**kwargs)

        compiled_to_path = temp_path / f'{to_rev}_compiled'
        kwargs = dict(
            repo_dir=to_rev_path,
            context=replay_context,
            overwrite_if_exists=False,
            skip_if_file_exists=False,
            output_dir=compiled_to_path,
        )
        logger.debug('Generate files with: %r', kwargs)
        generate_files(**kwargs)

        patch = git.diff(compiled_from_path, compiled_to_path)
        if not patch:
            logger.warning(f'No gif diff between {from_rev} and {to_rev} !')
            return None

        from_path_str = f'a{compiled_from_path}/'
        assert from_path_str in patch, f'{from_path_str!r} not found in patch: {patch}'
        patch = patch.replace(from_path_str, 'a/')

        to_path_str = f'b{compiled_to_path}/'
        assert to_path_str in patch, f'{to_path_str!r} not found in patch: {patch}'
        patch = patch.replace(to_path_str, 'b/')

        logger.info('Write patch file: %s', patch_file_path)
        patch_file_path.write_text(patch)
        return GenerateTemplatePatchResult(
            patch_file_path=patch_file_path, to_rev=to_rev, commit_date=commit_date
        )
