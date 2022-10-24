import logging
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError
from typing import Union

from manageprojects.subprocess_utils import verbose_check_call, verbose_check_output

logger = logging.getLogger(__name__)


class GitError(BaseException):
    """Base class for all git errors"""


class NoGitRepoError(GitError):
    def __init__(self, path):
        super().__init__(f'"{path}" is not a git repository')


class GitBinNotFoundError(GitError):
    def __init__(self):
        super().__init__('Git executable not found in PATH')


def get_git_root(path: Path):
    if len(path.parts) == 1 or not path.is_dir():
        return None

    if Path(path / '.git').is_dir():
        return path

    return get_git_root(path=path.parent)


class Git:
    def __init__(self, cwd: Union[Path, None]):
        self.cwd = cwd

        self.git_bin = which('git')
        if not self.git_bin:
            raise GitBinNotFoundError()

    def set_cwd_by_path(self, path: Path):
        self.git_root = get_git_root(path)
        if not self.git_root:
            raise NoGitRepoError(path)

    def verbose_check_call(self, *popenargs, cwd: Path = None, verbose=True):
        popenargs = [self.git_bin, *popenargs]
        return verbose_check_call(*popenargs, cwd=cwd or self.cwd, verbose=verbose)

    def verbose_check_output(self, *popenargs, cwd: Path = None, verbose=True, print_error=True):
        popenargs = [self.git_bin, *popenargs]
        return verbose_check_output(
            *popenargs, cwd=cwd or self.cwd, verbose=verbose, print_error=print_error
        )

    def get_current_hash(self, cwd: Path = None, verbose=True):
        output = self.verbose_check_output('rev-parse', '--short', 'HEAD', cwd=cwd, verbose=verbose)
        if rev := output.strip():
            return rev

        raise AssertionError(f'No git hash from: {output!r}')

    def get_patch(self, from_path, to_path):
        try:
            output = self.verbose_check_output('diff', from_path, to_path, print_error=False)
        except CalledProcessError as err:
            if err.returncode == 1:
                return err.stdout
            raise
        return output
