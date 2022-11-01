import dataclasses
import datetime
import logging
import shutil
from pathlib import Path
from typing import Optional

from cookiecutter.exceptions import NonTemplatedInputDirException
from cookiecutter.find import find_template
from rich import print  # noqa

from manageprojects.cookiecutter_interface import cookiecutter_generate_files
from manageprojects.git import Git
from manageprojects.utilities.temp_path import TemporaryDirectory


logger = logging.getLogger(__name__)


def cp_git_rev(git: Git, rev: str, dst: Path):
    git.git_verbose_check_call('reset', '--hard', rev)
    src_path = git.cwd
    shutil.copytree(src=src_path, dst=dst)

    # Just check if destination is okay:
    try:
        template_dir = find_template(repo_dir=dst)
    except NonTemplatedInputDirException:
        raise NonTemplatedInputDirException(f'Created repo {dst} from {src_path} is not valid!')
    else:
        assert template_dir, 'No template directory?!?'


@dataclasses.dataclass
class GenerateTemplatePatchResult:
    patch_file_path: Path

    from_rev: str
    from_rev_path: Path
    compiled_from_path: Path

    to_rev: str
    to_commit_date: datetime.datetime
    to_rev_path: Path
    compiled_to_path: Path


def generate_template_patch(
    project_path: Path,
    repo_path: Path,
    from_rev: str,
    replay_context: dict,
    cleanup: bool = True,  # Remove temp files if not exceptions happens
) -> Optional[GenerateTemplatePatchResult]:
    print(f'Generate update patch for project: {project_path} from {repo_path}')

    git = Git(cwd=repo_path, detect_root=True)
    git.git_verbose_check_call('fetch')
    to_rev = git.get_current_hash(verbose=False)
    to_commit_date = git.get_commit_date(verbose=False)
    print(f'Update from rev. {from_rev} to rev. {to_rev} ({to_commit_date})')

    if from_rev == to_rev:
        to_commit_date = git.get_commit_date()
        print(
            f'Latest version {from_rev!r}'
            f' from {to_commit_date} is already applied.'
            ' Nothing to update, ok.'
        )
        return None

    project_name = project_path.name

    patch_file_path = repo_path / '.manageprojects' / 'patches' / f'{from_rev}_{to_rev}.patch'
    print(f'Generate patch file: {patch_file_path}')

    with TemporaryDirectory(prefix=f'manageprojects_{project_name}_', cleanup=cleanup) as temp_path:

        template_name = repo_path.name
        from_rev_path = temp_path / from_rev / template_name
        to_rev_path = temp_path / to_rev / template_name

        cp_git_rev(git=git, rev=from_rev, dst=from_rev_path)
        cp_git_rev(git=git, rev=to_rev, dst=to_rev_path)

        compiled_from_path = temp_path / f'{from_rev}_compiled'
        cookiecutter_generate_files(
            repo_dir=from_rev_path,
            replay_context=replay_context,
            output_dir=compiled_from_path,
        )

        compiled_to_path = temp_path / f'{to_rev}_compiled'
        cookiecutter_generate_files(
            repo_dir=to_rev_path,
            replay_context=replay_context,
            output_dir=compiled_to_path,
        )

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
        patch_file_path.parent.mkdir(parents=True, exist_ok=True)
        patch_file_path.write_text(patch)
        return GenerateTemplatePatchResult(
            patch_file_path=patch_file_path,
            from_rev=from_rev,
            from_rev_path=from_rev_path,
            compiled_from_path=compiled_from_path,
            to_rev=to_rev,
            to_commit_date=to_commit_date,
            to_rev_path=to_rev_path,
            compiled_to_path=compiled_to_path,
        )
