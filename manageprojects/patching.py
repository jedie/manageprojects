import logging
import shutil
import tempfile
from pathlib import Path

from cookiecutter.main import cookiecutter
from rich import print  # noqa

import manageprojects
from manageprojects.git import Git
from manageprojects.path_utils import assert_is_dir
from manageprojects.subprocess_utils import verbose_check_call
from manageprojects.user_config import get_patch_path

logger = logging.getLogger(__name__)


class GitSwitcher:
    def __init__(self, git_url: str, sub_dir: str, git_src_path: Path):
        self.git_url = git_url
        self.sub_dir = sub_dir
        self.git_src_path = git_src_path
        self.git_src_path.mkdir(exist_ok=True)

        self._tmp = None
        self.src_path = None
        self.git = None

    def __enter__(self):
        self.git = Git(cwd=self.git_src_path)
        self.git.verbose_check_call('clone', '--no-checkout', self.git_url, self.git_src_path)
        verbose_check_call('ls', '-la', cwd=self.git_src_path)
        self.git.verbose_check_call('fetch')
        self.git.verbose_check_call('sparse-checkout', 'set', self.sub_dir)

        verbose_check_call('ls', '-la', cwd=self.git_src_path)
        verbose_check_call('tree', cwd=self.git_src_path)

        return self

    def cp_rev(self, rev: str, dst: Path):
        self.git.verbose_check_call('reset', '--hard', rev)
        verbose_check_call('git', 'reflog', cwd=self.git_src_path)
        verbose_check_call('ls', '-la', cwd=self.git_src_path)
        verbose_check_call('tree', cwd=self.git_src_path)
        src_path = self.git_src_path / self.sub_dir
        assert_is_dir(src_path)
        shutil.copytree(src=src_path, dst=dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False


def generate_template_patch():
    from_rev = '409f581'
    to_rev = 'ad03e9e'
    git_url = 'https://github.com/jedie/manageproject.git'
    template_name = 'minimal-python'
    template = f'manageprojects/project_templates/{template_name}'

    patch_path = get_patch_path()
    patch_file_path = patch_path / f'{template_name}_{from_rev}_{to_rev}.patch'

    tmpdir = '/tmp/manageproject_test'
    shutil.rmtree(tmpdir, ignore_errors=True)
    Path(tmpdir).mkdir()
    # with tempfile.TemporaryDirectory(prefix='manageprojects_') as tmpdir:

    temp_path = Path(tmpdir)
    git_src_path = temp_path / 'git_src'
    from_rev_path = temp_path / from_rev / template_name
    to_rev_path = temp_path / to_rev / template_name

    with GitSwitcher(git_url=git_url, sub_dir=template, git_src_path=git_src_path) as gw:
        gw.cp_rev(rev=from_rev, dst=from_rev_path)
        gw.cp_rev(rev=to_rev, dst=to_rev_path)

    verbose_check_call('tree', cwd=tmpdir)

    compiled_from_path = temp_path / f'{from_rev}_compiled'

    cookiecutter(
        template=template_name,
        replay=True,
        directory=from_rev_path,
        output_dir=compiled_from_path,
    )

    compiled_to_path = temp_path / f'{to_rev}_compiled'
    cookiecutter(
        template=template_name,
        replay=True,
        directory=to_rev_path,
        output_dir=compiled_to_path,
    )
    verbose_check_call('tree', cwd=tmpdir)
    # verbose_check_call('git', 'diff', compiled_from_path, compiled_to_path, cwd=tmpdir)

    git = Git(cwd=temp_path)
    patch = git.get_patch(compiled_from_path, compiled_to_path)
    if patch:
        logger.info('Write patch file: %s', patch_file_path)
        patch_file_path.write_text(patch)


if __name__ == '__main__':
    generate_template_patch()
