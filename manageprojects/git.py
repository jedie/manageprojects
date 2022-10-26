import datetime
import logging
from pathlib import Path
from shutil import which

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
    def __init__(self, *, cwd: Path, detect_root: bool = True):
        if detect_root:
            self.cwd = get_git_root(cwd)
            if not self.cwd:
                raise NoGitRepoError(cwd)
        else:
            self.cwd = cwd

        self.git_bin = which('git')
        if not self.git_bin:
            raise GitBinNotFoundError()

    def git_verbose_check_call(self, *popenargs, **kwargs):
        popenargs = [self.git_bin, *popenargs]
        return verbose_check_call(*popenargs, cwd=self.cwd, **kwargs)

    def git_verbose_check_output(self, *popenargs, **kwargs):
        popenargs = [self.git_bin, *popenargs]
        return verbose_check_output(*popenargs, cwd=self.cwd, **kwargs)

    def get_current_hash(self, commit='HEAD', verbose=True):
        output = self.git_verbose_check_output('rev-parse', '--short', commit, verbose=verbose)
        if rev := output.strip():
            return rev

        raise AssertionError(f'No git hash from: {output!r}')

    def get_commit_date(self, commit='HEAD', verbose=True):
        output = self.git_verbose_check_output(
            'show', '-s', '--format=%cI', commit, verbose=verbose
        )
        if raw_date := output.strip():
            # e.g.: "2022-10-25 20:43:10 +0200"
            return datetime.datetime.fromisoformat(raw_date)

        raise AssertionError(f'No commit date from: {output!r}')

    def get_patch(self, from_path, to_path):
        output = self.git_verbose_check_output('diff', from_path, to_path, exit_on_error=True)
        return output
