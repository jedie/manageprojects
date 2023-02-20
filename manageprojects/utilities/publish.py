import shutil
from collections.abc import Iterable
from importlib.metadata import version
from pathlib import Path

from bx_py_utils.path import assert_is_file


try:
    import tomllib  # New in Python 3.11
except ImportError:
    import tomli as tomllib

import sys

from packaging.version import Version
from rich import print  # noqa

from manageprojects.git import Git, GitError
from manageprojects.utilities.subprocess_utils import verbose_check_call


def exit_with_error(txt, hint=None):
    print(f'[red]ERROR: {txt}')
    if hint:
        print(f'[cyan](Hint: {hint})')
    print('[yellow]Abort.\n')
    sys.exit(-1)


def confirm(txt):
    print(f' [red]->[/red] [yellow]{txt}[/yellow]')
    print('>>>> [bold]Publish anyhow? (Y/N)', end=' ')
    if input().lower() not in ('y', 'j'):
        print('[cyan]Bye.\n')
        sys.exit(-1)


class PublisherGit:
    def __init__(self, *, package_path: Path, version: Version, possible_branch_names: Iterable[str]):
        self.package_path = package_path
        self.version = version
        self.possible_branch_names = possible_branch_names

        self.new_git_tag = f'v{version}'  # Created at the end

        print('\nDetect git repository...', end='')
        try:
            self.git = Git(cwd=package_path, detect_root=True)
        except GitError as err:
            exit_with_error(f'Git detection error: {err}')
            return

        if self.git.cwd != package_path:
            exit_with_error(f'Git path mismatch: {self.git.cwd} is not {package_path}')
        print('OK')

        print('\nAre we on the main branch...', end='')
        self.branch_name = self.git.get_current_branch_name(verbose=False)
        if self.branch_name not in possible_branch_names:
            confirm(f'The current git branch "[bold]{self.branch_name}[/bold]" seems to be wrong!')
        else:
            print('OK')

    def fast_checks(self):
        print('\nIs repository clean...', end='')
        if changes := self.git.status(verbose=False):
            confirm(f'Git changes: {changes}')
        else:
            print('OK')

        print(f'\ncheck git tag {self.version}...', end='')
        existing_versions = self.git.get_version_from_tags(
            dev_release=True, pre_release=True, verbose=False, exit_on_error=True
        )
        if self.version in existing_versions:
            exit_with_error(f'git tag "[bold]{self.version}[/bold]" already exists!')
        print('OK')

    def slow_checks(self):
        print('\nLocal repository up-to-date: fetch origin...', end='')
        self.git.git_verbose_check_call('fetch', 'origin', verbose=False)
        print('compare...', end='')
        output = self.git.git_verbose_check_output(
            'log', f'HEAD..origin/{self.branch_name}', '--oneline', verbose=False
        )
        if output != '':
            exit_with_error(f'git repro is not up-to-date:\n{output}')
        else:
            print('push...', end='')
            output = self.git.git_verbose_check_output('push', 'origin', self.branch_name, verbose=False)
            if 'up-to-date' not in output:
                exit_with_error(f'git repro is not up-to-date:\n{output}')
        print('OK')

    def finalize(self):
        self.git.tag(self.new_git_tag, message=f'publish version {self.version}')
        print('\ngit push tag to server')
        self.git.push(tags=True)


def clean_version(version: str) -> Version:
    assert version
    assert isinstance(version, str)
    return Version(version)


def check_version(*, module, package_path: Path) -> Version:
    module_version = clean_version(module.__version__)
    pyproject_toml_path = Path(package_path, 'pyproject.toml')
    assert_is_file(pyproject_toml_path)

    installed_version = clean_version(version(module.__name__))
    if module_version != installed_version:
        exit_with_error(
            f'Version mismatch: current version {module_version} is not the installed one: {installed_version}',
            hint='Install package and run publish again',
        )

    pyproject_toml = tomllib.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
    pyproject_version = clean_version(pyproject_toml['project']['version'])
    if pyproject_version != installed_version:
        exit_with_error(
            (
                f'Version mismatch:'
                f' pyproject.toml version {pyproject_version} is not the installed one: {installed_version}'
            ),
            hint='Install package and run publish again',
        )

    return module_version


def build(package_path) -> None:
    print('\nCleanup old builds...', end='')

    def rmtree(path):
        if path.exists():
            print(f'remove old "{path.name}"...', end='')
            shutil.rmtree(path)

    rmtree(package_path / 'dist')
    rmtree(package_path / 'build')
    print('OK')

    verbose_check_call(sys.executable, '-m', 'build')


def publish_package(*, module, package_path: Path, possible_branch_names=('main', 'master')):
    """
    Build and upload a project to PyPi

    TODO: Add all checks from:
        https://github.com/jedie/poetry-publish/blob/main/poetry_publish/publish.py
    """
    # Version number correct?
    version: Version = check_version(module=module, package_path=package_path)
    if version.is_devrelease or version.is_prerelease:
        confirm(f'Current version {version} is dev/pre release!')

    pgit = PublisherGit(package_path=package_path, version=version, possible_branch_names=possible_branch_names)
    pgit.fast_checks()

    # Build distribution from package:
    build(package_path)

    verbose_check_call('twine', 'check', '--strict', 'dist/*')

    # Are local git repository up-to-date with remote?
    pgit.slow_checks()

    verbose_check_call('twine', 'upload', 'dist/*')

    # Push the new tag to remote
    pgit.finalize()
