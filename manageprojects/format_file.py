import dataclasses
from pathlib import Path
from typing import Optional

from bx_py_utils.dict_utils import dict_get
from cli_base.cli_tools.git import Git, GitError, NoGitRepoError
from cli_base.cli_tools.subprocess_utils import ToolsExecutor
from editorconfig import EditorConfigError, get_properties
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from rich import print  # noqa
from rich.pretty import pprint

from manageprojects.constants import FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH, FORMAT_PY_FILE_DEFAULT_MIN_PYTON_VERSION
from manageprojects.exceptions import NoPyProjectTomlFound
from manageprojects.utilities.pyproject_toml import TomlDocument, get_pyproject_toml


MAX_PY3_VER = 15


@dataclasses.dataclass
class GitInfo:
    cwd: Path
    main_branch_name: str


@dataclasses.dataclass
class PyProjectInfo:
    py_min_ver: Version
    pyproject_toml_path: Optional[Path] = None
    raw_py_ver_req: Optional[str] = None


@dataclasses.dataclass
class Config:
    git_info: Optional[GitInfo]
    pyproject_info: PyProjectInfo
    max_line_length: int

    @property
    def py_ver_str(self) -> Optional[str]:
        if pyproject_info := self.pyproject_info:
            return f'py{pyproject_info.py_min_ver.major}{pyproject_info.py_min_ver.minor}'

    @property
    def project_root_path(self) -> Optional[Path]:
        if git_info := self.git_info:
            if cwd := git_info.cwd:
                return cwd

        if pyproject_toml_path := self.pyproject_info.pyproject_toml_path:
            return pyproject_toml_path.parent

    @property
    def main_branch_name(self) -> Optional[str]:
        if git_info := self.git_info:
            return git_info.main_branch_name


def get_git_info(file_path: Path) -> Optional[GitInfo]:
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
                cwd=git.cwd,
                main_branch_name=main_branch_name,
            )


def get_py_min_version(raw_py_ver_req) -> Optional[Version]:
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


def get_editorconfig_max_line_length(file_path) -> Optional[int]:
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
    default_min_py_version=FORMAT_PY_FILE_DEFAULT_MIN_PYTON_VERSION,
    default_max_line_length=FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH,
) -> Config:
    config = Config(
        git_info=get_git_info(file_path),
        pyproject_info=get_pyproject_info(file_path, default_min_py_version),
        max_line_length=get_editorconfig_max_line_length(file_path) or default_max_line_length,
    )
    pprint(config)
    return config


def run_pyupgrade(tools_executor, file_path, config):
    pyver_arg = f'--{config.py_ver_str}-plus'
    tools_executor.verbose_check_output(
        'pyupgrade',
        '--exit-zero-even-if-changed',
        pyver_arg,
        file_path,
    )


def run_autoflake(tools_executor, file_path, config, remove_all_unused_imports):
    # TODO: Remove if isort can do the job: https://github.com/PyCQA/isort/issues/1105
    args = ['autoflake', '--in-place']
    if remove_all_unused_imports:
        args.append('--remove-all-unused-imports')
    args.append(file_path)
    tools_executor.verbose_check_output(*args)


def run_darker(tools_executor, file_path, config, darker_prefixes):
    if darker_prefixes:
        # darker/black will not fix e.g.:
        #   "E302 expected 2 blank lines"
        #   "E303 too many blank lines (4)"
        # work-a-round: run autopep8 only for these fixes ;)
        tools_executor.verbose_check_output(
            'autopep8',
            '--ignore-local-config',
            '--select',
            darker_prefixes,
            f'--max-line-length={config.max_line_length}',
            '--in-place',
            str(file_path),
        )

    tools_executor.verbose_check_output(
        'darker',
        '--flynt',
        '--isort',
        '--skip-string-normalization',
        '--revision',
        f'{config.main_branch_name}...',
        '--line-length',
        str(config.max_line_length),
        '--target-version',
        config.py_ver_str,
        file_path,
    )


def run_autopep8(tools_executor, file_path, config):
    tools_executor.verbose_check_output(
        'autopep8',
        '--ignore-local-config',
        '--max-line-length',
        str(config.max_line_length),
        '--aggressive',
        '--aggressive',
        '--in-place',
        file_path,
    )


def run_flake8(tools_executor, file_path, config):
    tools_executor.verbose_check_output(
        'flake8',
        '--max-line-length',
        str(config.max_line_length),
        file_path,
    )


def run_pyflakes(tools_executor, file_path, config):
    tools_executor.verbose_check_output('pyflakes', file_path)


def run_codespell(tools_executor, file_path, config):
    tools_executor.verbose_check_output('codespell', file_path)


def run_mypy(tools_executor, file_path, config):
    tools_executor.verbose_check_output(
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
    darker_prefixes: str,
    remove_all_unused_imports: bool,
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

    run_pyupgrade(tools_executor, file_path, config)
    run_autoflake(
        tools_executor,
        file_path,
        config,
        remove_all_unused_imports=remove_all_unused_imports,
    )

    if config.main_branch_name:
        run_darker(tools_executor, file_path, config, darker_prefixes)
    else:
        run_autopep8(tools_executor, file_path, config)

    run_flake8(tools_executor, file_path, config)
    run_pyflakes(tools_executor, file_path, config)
    run_codespell(tools_executor, file_path, config)
    run_mypy(tools_executor, file_path, config)

    print('\n')

    changed = old_content != abs_file_path.read_bytes()
    if changed:
        print(f'[green bold]*** File [blue]{abs_file_path}[/blue] successfully updated. ***')
    else:
        print(f'[green bold]*** File [blue]{abs_file_path}[/blue] needs to changes, ok. ***')
