import datetime
import logging
import subprocess  # nosec B404
from pathlib import Path
from shutil import which

from bx_py_utils.path import assert_is_file

from manageprojects.utilities.subprocess_utils import verbose_check_call, verbose_check_output


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
        return verbose_check_call(
            *popenargs,
            cwd=self.cwd,
            env=dict(),  # Empty env -> no translated git command output ;)
            **kwargs,
        )

    def git_verbose_check_output(self, *popenargs, **kwargs):
        popenargs = [self.git_bin, *popenargs]
        return verbose_check_output(
            *popenargs,
            cwd=self.cwd,
            env=dict(),  # Empty env -> no translated git command output ;)
            **kwargs,
        )

    def git_verbose_output(
        self, *popenargs, exit_on_error=False, ignore_process_error=True, **kwargs
    ):
        popenargs = [self.git_bin, *popenargs]
        try:
            return verbose_check_output(
                *popenargs, cwd=self.cwd, exit_on_error=exit_on_error, **kwargs
            )
        except subprocess.CalledProcessError as err:
            if ignore_process_error:
                return err.stdout
            raise

    def get_current_hash(self, commit='HEAD', verbose=True) -> str:
        output = self.git_verbose_check_output('rev-parse', '--short', commit, verbose=verbose)
        if git_hash := output.strip():
            assert len(git_hash) == 7, f'No git hash from: {output!r}'
            return git_hash

        raise AssertionError(f'No git hash from: {output!r}')

    def get_commit_date(self, commit='HEAD', verbose=True) -> datetime.datetime:
        output = self.git_verbose_check_output(
            'show', '-s', '--format=%cI', commit, verbose=verbose
        )
        raw_date = output.strip()
        # e.g.: "2022-10-25 20:43:10 +0200"
        return datetime.datetime.fromisoformat(raw_date)

    def diff(
        self,
        reference1,
        reference2,
        no_color=True,
        indent_heuristic=False,
        irreversible_delete=True,
        verbose=True,
    ) -> str:
        # https://git-scm.com/docs/git-diff
        args = []
        if no_color:
            args.append('--no-color')

        if not indent_heuristic:
            args.append('--no-indent-heuristic')

        if irreversible_delete:
            args.append('--irreversible-delete')

        output = self.git_verbose_output('diff', *args, reference1, reference2, verbose=verbose)
        return output

    def apply(self, patch_path, verbose=True):
        # https://git-scm.com/docs/git-apply
        self.git_verbose_check_call(
            'apply',
            '--reject',
            '--ignore-whitespace',
            '--whitespace=fix',
            '-C1',
            '--recount',
            '--stat',
            '--summary',
            '--verbose',
            '--apply',
            patch_path,
            verbose=verbose,
        )

    def init(
        self,
        branch_name='main',
        user_name='manageprojects',
        user_email='manageprojects@test.tld',
        verbose=True,
    ) -> Path:
        output = self.git_verbose_check_output(
            'init', '-b', branch_name, verbose=verbose, exit_on_error=True
        )
        assert 'initialized' in output.lower(), f'Seems there is an error: {output}'
        self.cwd = get_git_root(self.cwd)

        self.config('user.name', user_name, scope='local', verbose=verbose)
        self.config('user.email', user_email, scope='local', verbose=verbose)

        return self.cwd

    def config(self, key, value, scope='local', verbose=True):
        assert scope in ('global', 'system', 'local')
        output = self.git_verbose_check_output(
            'config', f'--{scope}', key, value, verbose=verbose, exit_on_error=True
        )
        return output.strip()

    def get_config(self, key, verbose=True):
        if key in self.list_config_keys(verbose=verbose):
            output = self.git_verbose_check_output(
                'config', '--get', key, verbose=verbose, exit_on_error=False
            )
            return output.strip()

    def list_config_keys(self, verbose=False) -> set:
        output = self.git_verbose_check_output(
            'config', '--list', '--name-only', verbose=verbose, exit_on_error=False
        )
        keys = {item.strip() for item in output.splitlines() if item.strip()}
        return keys

    def add(self, spec, verbose=True) -> None:
        output = self.git_verbose_check_output('add', spec, verbose=verbose, exit_on_error=True)
        assert not output, f'Seems there is an error: {output}'

    def commit(self, comment, verbose=True) -> str:
        output = self.git_verbose_check_output(
            'commit', '--message', comment, verbose=verbose, exit_on_error=True
        )
        assert comment in output, f'Seems there is an error: {output}'
        return output

    def reflog(self, verbose=True) -> str:
        return self.git_verbose_check_output('reflog', verbose=verbose, exit_on_error=True)

    def log(self, format='%h - %an, %ar : %s', verbose=True) -> list[str]:
        output = self.git_verbose_check_output(
            'log', f'--pretty=format:{format}', verbose=verbose, exit_on_error=True
        )
        lines = output.splitlines()
        return lines

    def tag(self, git_tag: str, message: str):
        self.git_verbose_check_call('tag', '-a', git_tag, '-m', message)

    def push(self, tags=False):
        if tags:
            args = ['--tags']
        else:
            args = []

        self.git_verbose_check_call('push', *args)

    def tag_list(self, verbose=True, exit_on_error=True) -> list[str]:
        output = self.git_verbose_check_output('tag', verbose=verbose, exit_on_error=exit_on_error)
        lines = output.splitlines()
        return lines

    def ls_files(self, verbose=True) -> list[Path]:
        output = self.git_verbose_check_output('ls-files', verbose=verbose, exit_on_error=True)
        file_paths = []
        for line in output.splitlines():
            file_path = self.cwd / line
            assert_is_file(file_path)
            file_paths.append(file_path)
        return sorted(file_paths)

    def print_file_list(self, out_func=print, verbose=True) -> None:
        for item in self.ls_files(verbose=verbose):
            out_func(f'* "{item.relative_to(self.cwd)}"')

    def reset(self, *, commit, hard=True, verbose=True) -> None:
        args = ['reset']
        if hard:
            args.append('--hard')
        args.append(commit)
        output = self.git_verbose_check_output(*args, verbose=verbose, exit_on_error=True)
        test_str = f'HEAD is now at {commit} '
        assert output.startswith(
            test_str
        ), f'Reset error: {output!r} does not start with {test_str!r}'
