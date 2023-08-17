import shutil
import tempfile
from collections.abc import Iterable
from importlib.metadata import version
from pathlib import Path
from typing import Optional

from bx_py_utils.dict_utils import dict_get
from bx_py_utils.path import assert_is_file


try:
    import tomllib  # New in Python 3.11
except ImportError:
    import tomli as tomllib

import sys

from cli_base.cli_tools.git import Git, GitError
from cli_base.cli_tools.subprocess_utils import verbose_check_call, verbose_check_output
from packaging.version import Version
from rich import print  # noqa


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
    def __init__(
        self, *, package_path: Path, version: Version, possible_branch_names: Iterable[str], tag_msg_log_format: str
    ):
        self.package_path = package_path
        self.version = version
        self.possible_branch_names = possible_branch_names
        self.tag_msg_log_format = tag_msg_log_format

        self.git_tag_msg = None  # Set later

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
        git_tag_infos = self.git.get_tag_infos()
        if git_tag_infos.exists(version=self.version):
            exit_with_error(f'git tag for "[bold]{self.version}[/bold]" already exists!')
        print('OK')

        print('\nCollect tag change message...', end='')
        last_tag = git_tag_infos.get_last_release()
        if not last_tag:
            # Just collect all commits
            commit1 = None
            commit2 = None
        else:
            commit1 = 'HEAD'
            commit2 = last_tag.raw_tag
            print(f'[blue]{commit1}...{commit2}[/blue]', end=' ')

        log_lines = self.git.log(
            format=self.tag_msg_log_format,
            no_merges=True,
            commit1=commit1,
            commit2=commit2,
            verbose=False,
            exit_on_error=True,
        )
        change_msg = '\n'.join(f' * {line}' for line in log_lines)
        print('done:')
        print(change_msg)
        if last_tag:
            self.git_tag_msg = (
                f'publish version v{self.version} with these changes (since {last_tag.version_tag}):\n\n{change_msg}\n'
            )
        else:
            self.git_tag_msg = f'publish version v{self.version} with these changes:\n\n{change_msg}\n'

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
        self.git.tag(f'v{self.version}', message=self.git_tag_msg, verbose=True)

        print('\ngit push tag to server')
        self.git.push(tags=True, verbose=True)


def clean_version(version: str) -> Version:
    assert version
    assert isinstance(version, str)
    return Version(version)


def setuptools_dynamic_version(*, pyproject_toml: dict, pyproject_toml_path: Path) -> Optional[Version]:
    dynamic = dict_get(pyproject_toml, 'project', 'dynamic')
    if dynamic and 'version' in dynamic:
        if dict_get(pyproject_toml, 'tool', 'setuptools', 'dynamic', 'version'):
            # Project used "dynamic metadata" from setuptools for the version
            from setuptools.config.pyprojecttoml import read_configuration

            setuptools_pyproject_toml = read_configuration(pyproject_toml_path)
            if ver_str := dict_get(setuptools_pyproject_toml, 'project', 'version'):
                return clean_version(ver_str)


def get_pyproject_toml_version(package_path: Path) -> Optional[Version]:
    pyproject_toml_path = Path(package_path, 'pyproject.toml')
    assert_is_file(pyproject_toml_path)

    pyproject_toml = tomllib.loads(pyproject_toml_path.read_text(encoding='UTF-8'))

    ver_str = dict_get(pyproject_toml, 'project', 'version')
    if not ver_str:
        ver_str = dict_get(pyproject_toml, 'tool', 'poetry', 'version')

    if ver_str:
        return clean_version(ver_str)

    return setuptools_dynamic_version(pyproject_toml=pyproject_toml, pyproject_toml_path=pyproject_toml_path)


def check_version(*, module, package_path: Path, distribution_name: Optional[str] = None) -> Version:
    if not distribution_name:
        distribution_name = module.__name__

    module_version = clean_version(module.__version__)
    installed_version = clean_version(version(distribution_name))
    if module_version != installed_version:
        exit_with_error(
            f'Version mismatch: current version {module_version} is not the installed one: {installed_version}',
            hint='Install package and run publish again',
        )

    pyproject_version = get_pyproject_toml_version(package_path)
    if not pyproject_version:
        confirm('Can not get package version from pyproject.toml')
    elif pyproject_version != installed_version:
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

    if Path(package_path / 'poetry.lock').is_file():
        # Poetry used -> build with it
        output = verbose_check_output('poetry', 'build', verbose=True, exit_on_error=True)
    else:
        # use normal build
        output = verbose_check_output(sys.executable, '-m', 'build', verbose=True, exit_on_error=True)

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', prefix=f'{package_path.name}_', encoding='utf-8', delete=False
    ) as temp_file:
        temp_file.write(output)
    print(f'[yellow]Output written to: [bold]{temp_file.name}')


def publish_package(
    *,
    module,
    package_path: Path,
    possible_branch_names: tuple[str] = ('main', 'master'),
    tag_msg_log_format: str = '%h %as %s',
    distribution_name: Optional[str] = None,  # Must be given, if it's not == module.__name__
) -> None:
    """
    Build and upload (with twine) a project to PyPi with many pre-checks:

     * Has correct version number?
     * Is on main branch and up-to-date with origin?
     * Check if current version already published
     * Build a git tag based on current package version
     * Adds change messages since last release to git tag message

    Designed to be useful for external packages.
    Some checks result in a hard exit, but some can be manually confirmed from the user to continue publishing.
    """
    # Version number correct?
    version: Version = check_version(module=module, package_path=package_path, distribution_name=distribution_name)
    if version.is_devrelease or version.is_prerelease:
        confirm(f'Current version {version} is dev/pre release!')

    pgit = PublisherGit(
        package_path=package_path,
        version=version,
        possible_branch_names=possible_branch_names,
        tag_msg_log_format=tag_msg_log_format,
    )
    pgit.fast_checks()

    # Build distribution from package:
    build(package_path)

    verbose_check_call('twine', 'check', '--strict', 'dist/*')

    # Are local git repository up-to-date with remote?
    pgit.slow_checks()

    verbose_check_call('twine', 'upload', 'dist/*')

    # Push the new tag to remote
    pgit.finalize()
