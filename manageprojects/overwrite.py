import filecmp
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

from bx_py_utils.path import assert_is_dir
from cli_base.cli_tools.git import Git
from rich import print

from manageprojects.cookiecutter_api import execute_cookiecutter
from manageprojects.data_classes import OverwriteResult
from manageprojects.utilities.temp_path import TemporaryDirectory


logger = logging.getLogger(__name__)


def overwrite_project(
    *,
    git: Git,
    project_path: Path,
    template: str,  # CookieCutter Template path or GitHub url
    from_rev: str,
    replay_context: dict,
    directory: Optional[str] = None,  # Directory name of the CookieCutter Template
    password: Optional[str] = None,
    config_file: Optional[Path] = None,  # Optional path to 'cookiecutter_config.yaml'
    cleanup: bool = True,  # Remove temp files if not exceptions happens
    no_input: bool = False,  # Prompt the user at command line for manual configuration?
) -> OverwriteResult:
    print(f'Update by overwrite project: {project_path} from {template}')

    status = git.status()
    if status:
        print(f'Abort: project {project_path} is not clean:', file=sys.stderr)
        for flag, filepath in status:
            print(flag, filepath)
        sys.exit(1)

    extra_context = replay_context.get('cookiecutter')
    if not extra_context:
        print('WARNING: No "cookiecutter" in replay context!')

    project_name = project_path.name
    with TemporaryDirectory(prefix=f'manageprojects_{project_name}_', cleanup=cleanup) as temp_path:
        print(f'Compile cookiecutter template in the current version here: {temp_path}')
        print('Use extra context:')
        print(extra_context)
        to_rev_context, to_rev_dst_path, to_rev_repo_path = execute_cookiecutter(
            template=template,
            directory=directory,
            output_dir=temp_path,
            no_input=no_input,
            extra_context=extra_context,
            checkout=None,  # Checkout HEAD/main revision
            password=password,
            config_file=config_file,
        )
        assert_is_dir(to_rev_repo_path)

        git = Git(cwd=to_rev_repo_path, detect_root=True)
        to_rev = git.get_current_hash(verbose=False)
        to_commit_date = git.get_commit_date(verbose=False)
        print(f'Update from rev. {from_rev} to rev. {to_rev} ({to_commit_date})')

        updated_file_count = 0
        for src_file_path in to_rev_dst_path.rglob('*'):
            if not src_file_path.is_file():
                continue

            dst_file_path = project_path / src_file_path.relative_to(to_rev_dst_path)
            if not dst_file_path.exists():
                print(f'NEW file: {dst_file_path}')
            elif filecmp.cmp(dst_file_path, src_file_path, shallow=False):
                print(f'Skip unchanged file: {dst_file_path}, ok.')
                continue
            else:
                print(f'UPDATE file: {dst_file_path}')

            if not dst_file_path.parent.exists():
                dst_file_path.parent.mkdir(parents=True)

            shutil.copyfile(src_file_path, dst_file_path)
            updated_file_count += 1

    logger.info('%i files updated by overwriting', updated_file_count)

    if updated_file_count > 0:
        return OverwriteResult(to_rev=to_rev, to_commit_date=to_commit_date)
