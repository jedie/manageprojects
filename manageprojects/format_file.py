import dataclasses
import logging
from pathlib import Path
import subprocess

from bx_py_utils.dict_utils import dict_get
from cli_base.cli_tools.git import Git, GitError, NoGitRepoError
from cli_base.cli_tools.subprocess_utils import ToolsExecutor as OriginalToolsExecutor
from editorconfig import EditorConfigError, get_properties
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from rich import print  # noqa
from rich.pretty import pprint

from manageprojects.constants import FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH, FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION
from manageprojects.exceptions import NoPyProjectTomlFound
from manageprojects.utilities.pyproject_toml import TomlDocument, get_pyproject_toml


logger = logging.getLogger(__name__)

MAX_PY3_VER = 15


class ToolsExecutor(OriginalToolsExecutor):
    def verbose_check_call(self, *args, **kwargs):
        try:
            super().verbose_check_call(*args, **kwargs)
        except subprocess.CalledProcessError:
            pass  # Info print is already done


@dataclasses.dataclass
class GitInfo:
    git: Git
    main_branch_name: str


@dataclasses.dataclass
class PyProjectInfo:
    py_min_ver: Version
    pyproject_toml_path: Path | None = None
    raw_py_ver_req: str | None = None


@dataclasses.dataclass
class Config:
    git_info: GitInfo | None
    pyproject_info: PyProjectInfo
    max_line_length: int

    @property
    def py_ver_str(self) -> str | None:
        if pyproject_info := self.pyproject_info:
            return f'py{pyproject_info.py_min_ver.major}{pyproject_info.py_min_ver.minor}'

    @property
    def project_root_path(self) -> Path | None:
        if git_info := self.git_info:
            if cwd := git_info.git.cwd:
                return cwd

        if pyproject_toml_path := self.pyproject_info.pyproject_toml_path:
            return pyproject_toml_path.parent

    @property
    def main_branch_name(self) -> str | None:
        if git_info := self.git_info:
            return git_info.main_branch_name


def get_git_info(file_path: Path) -> GitInfo | None:
    try:
        git = Git(cwd=file_path.parent, detect_root=True)
    except NoGitRepoError:
        print('File is not under Git version control')
    else:
        try:
            main_branch_name = git.get_main_branch_name(verbose=False)
        except GitError as err:
            print(f'Error: {err}')
        else:
            print(f'Git main branch name: {main_branch_name!r} from: {git.cwd}')
            return GitInfo(
                git=git,
                main_branch_name=main_branch_name,
            )


def get_py_min_version(raw_py_ver_req) -> Version | None:
    specifier = SpecifierSet(raw_py_ver_req)

    # FIXME: How can this been simpler?
    for minor in range(MAX_PY3_VER):
        py_min_ver = f'3.{minor}'
        if specifier.contains(py_min_ver):
            py_min_ver = Version(py_min_ver)
            print(f'Min. Python version: {py_min_ver}')
            return py_min_ver

    print(f'Error getting min. python version from: {raw_py_ver_req!r} ({specifier})')


def get_pyproject_info(file_path: Path, default_min_py_version: str) -> PyProjectInfo:
    pyproject_info = PyProjectInfo(
        py_min_ver=Version(default_min_py_version),
    )

    try:
        toml_document: TomlDocument = get_pyproject_toml(file_path=file_path)
    except NoPyProjectTomlFound as err:
        print(err)
        print('Cannot detect the minimal Python version')
        return pyproject_info

    pyproject_info.pyproject_toml_path = toml_document.file_path
    data = toml_document.doc.unwrap()  # TOMLDocument -> dict

    if raw_py_ver_req := dict_get(data, 'project', 'requires-python'):
        # [project]
        # requires-python = ">=3.9,<4"
        pyproject_info.raw_py_ver_req = raw_py_ver_req
    elif raw_py_ver_req := dict_get(data, 'tool', 'poetry', 'dependencies', 'python'):
        # [tool.poetry.dependencies]
        # python = '>=3.9,<4.0.0'
        pyproject_info.raw_py_ver_req = raw_py_ver_req

    if pyproject_info.raw_py_ver_req:
        if py_min_ver := get_py_min_version(pyproject_info.raw_py_ver_req):
            pyproject_info.py_min_ver = py_min_ver

    return pyproject_info


def get_editorconfig_max_line_length(file_path) -> int | None:
    try:
        options = get_properties(file_path)
    except EditorConfigError as err:
        print(f'EditorConfig error: {err}')
    else:
        max_line_length = options.get('max_line_length')
        if not max_line_length:
            print(f'No "max_line_length" in EditorConfig: {dict(options)}')
        else:
            max_line_length = int(max_line_length)
            print(f'Get max_line_length from EditorConfig: {max_line_length!r}')
            return max_line_length


def get_config(
    file_path,
    default_min_py_version=FORMAT_PY_FILE_DEFAULT_MIN_PYTHON_VERSION,
    default_max_line_length=FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
) -> Config:
    config = Config(
        git_info=get_git_info(file_path),
        pyproject_info=get_pyproject_info(file_path, default_min_py_version),
        max_line_length=get_editorconfig_max_line_length(file_path) or default_max_line_length,
    )
    pprint(config)
    return config


def format_complete_file(tools_executor, file_path, config: Config):
    tools_executor.verbose_check_call(
        'ruff',
        'format',
        '--target-version',
        config.py_ver_str,
        file_path,
    )


def parse_ranges(git_diff_output: str) -> list:
    line_changes = []
    for line in git_diff_output.splitlines():
        if not line.startswith('@@'):
            continue

        line_infos = line.split('@@')[1].strip().split(' ')
        temp = []
        for line_info in line_infos:
            line_info = line_info.strip('+-')
            if ',' in line_info:
                start_line, line_count = map(int, line_info.split(','))
            else:
                start_line, line_count = int(line_info), 1

            if start_line == 0:
                start_line = 1  # ruff starts line numbers from 1, not 0

            temp.append(start_line)
            temp.append(start_line + line_count)
        line_changes.append((min(temp), max(temp)))
    return line_changes


def merge_ranges(ranges: list, max_distance: int = 1) -> list:
    """
    >>> merge_ranges([(1,2), (3,4), (10,11), (20, 25), (21, 26)])
    [(1, 4), (10, 11), (20, 26)]
    """
    merged = []
    for start, end in sorted(ranges):
        if merged and start - merged[-1][1] <= max_distance:
            # Extend the last range if within max_distance
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            # Otherwise, add a new range
            merged.append((start, end))
    return merged


def format_only_changed_lines(tools_executor, file_path, config: Config, max_distance=2):
    # Use darker after v3 release, see: https://github.com/akaihola/darker/milestones

    git: Git = config.git_info.git
    target = f'origin/{config.main_branch_name}'

    git_diff_output = git.git_verbose_check_output('diff', target, '--unified=0', file_path)
    logger.debug('Git diff output: %s', git_diff_output)
    ranges = parse_ranges(git_diff_output)
    print(f'All git diff code ranges: {ranges}')

    if not ranges:
        # TODO: Check if file is part of git repository:
        #       If not, then format it. If yes, then skip.
        tools_executor.verbose_check_call(
            'ruff',
            'format',
            '--target-version',
            config.py_ver_str,
            file_path,
            verbose=False,
        )
    else:
        print('Apply code formatter only to changed lines (in reversed order):')
        ranges = merge_ranges(ranges, max_distance=max_distance)
        for start, end in reversed(ranges):
            print(f'Processing range: {start} - {end}', end=' - ')
            tools_executor.verbose_check_call(
                'ruff',
                'format',
                '--target-version',
                config.py_ver_str,
                file_path,
                f'--range={start}-{end}',
                verbose=False,
            )

    print('\n\nFix imports and remove unused imports:')
    tools_executor.verbose_check_call(
        'ruff',
        'check',
        '--target-version',
        config.py_ver_str,
        '--select',
        'I001,F401',  # I001: Import sorting (from isort) + F401: Unused imports (from pyflakes)
        '--fix',
        '--unsafe-fixes',
        file_path,
    )


def run_file_check(tools_executor, file_path, config: Config):
    tools_executor.verbose_check_call(
        'ruff',
        'check',
        '--target-version',
        config.py_ver_str,
        file_path,
    )


def run_codespell(tools_executor, file_path, config: Config):
    tools_executor.verbose_check_call('codespell', file_path)


def run_mypy(tools_executor, file_path, config: Config):
    tools_executor.verbose_check_call(
        'mypy',
        '--ignore-missing-imports',
        '--follow-imports',
        'skip',
        '--allow-redefinition',  # https://github.com/python/mypy/issues/7165
        str(file_path),
    )


def format_one_file(
    *,
    default_min_py_version: str,
    default_max_line_length: int,
    file_path: Path,
) -> None:
    file_path = file_path.resolve()
    print(f'\nApply code formatter to: {file_path}')
    if file_path.suffix.lower() != '.py':
        print('Skip non-Python file ;)')
        return

    abs_file_path = file_path.absolute()

    old_content = abs_file_path.read_bytes()

    config = get_config(
        abs_file_path,
        default_min_py_version=default_min_py_version,
        default_max_line_length=default_max_line_length,
    )
    if cwd := config.project_root_path:
        file_path = abs_file_path.relative_to(cwd)

    tools_executor = ToolsExecutor(cwd=config.project_root_path)

    print('\n')

    if config.main_branch_name:
        # We have a Git repository, so we can format only changed lines
        format_only_changed_lines(tools_executor, file_path, config)
    else:
        # Run full formatting the whole file
        format_complete_file(tools_executor, file_path, config)

    run_file_check(tools_executor, file_path, config)
    run_codespell(tools_executor, file_path, config)
    run_mypy(tools_executor, file_path, config)

    print('\n')

    changed = old_content != abs_file_path.read_bytes()
    if changed:
        print(f'[green bold]*** File [blue]{abs_file_path}[/blue] successfully updated. ***')
    else:
        print(f'[green bold]*** File [blue]{abs_file_path}[/blue] needs to changes, ok. ***')
