import inspect
from pathlib import Path
from unittest import TestCase

from cli_base.cli_tools.test_utils.logs import AssertLogs
from packaging.version import Version

from manageprojects.cli_dev import PACKAGE_ROOT
from manageprojects.constants import PY_BIN_PATH
from manageprojects.format_file import (
    Config,
    GitInfo,
    PyProjectInfo,
    format_one_file,
    get_config,
    get_editorconfig_max_line_length,
    get_git_info,
    get_pyproject_info,
    parse_ranges,
)
from manageprojects.test_utils.subprocess import SimpleRunReturnCallback, SubprocessCallMock
from manageprojects.tests.base import GIT_BIN_PARENT
from manageprojects.utilities.temp_path import TemporaryDirectory


class FormatFileTestCase(TestCase):
    maxDiff = None

    def test_parse_ranges(self):
        git_diff_output = inspect.cleandoc("""
            diff --git a/manageprojects/format_file.py b/manageprojects/format_file.py
            index 0d480a8..1b29799 100644
            --- a/manageprojects/format_file.py
            +++ b/manageprojects/format_file.py
            @@ -1,0 +2 @@ import dataclasses
            +import re
            @@ -32 +33 @@ class GitInfo:
            -    cwd: Path
            +    git: Git
            @@ -293,6 +259,0 @@ def format_one_file(
            -    run_autoflake(
            -        tools_executor,
            -        file_path,
            -        config,
            -        remove_all_unused_imports=remove_all_unused_imports,
            -    )
        """)
        ranges = parse_ranges(git_diff_output)
        self.assertEqual(
            ranges,
            [
                (1, 3),
                (32, 34),
                (259, 299),
            ],
        )

    def test_get_git_info(self):
        with AssertLogs(self, loggers=('cli_base',)):
            git_info = get_git_info(file_path=Path(__file__))
            self.assertIsInstance(git_info, GitInfo)
            self.assertEqual(git_info.main_branch_name, 'main')

            with TemporaryDirectory(prefix='test_get_main_branch_name') as temp_path:
                self.assertIsNone(get_git_info(file_path=temp_path))

    def test_get_pyproject_info(self):
        with TemporaryDirectory(prefix='test_get_pyproject_info') as temp_path:
            self.assertEqual(
                get_pyproject_info(temp_path, default_min_py_version='1.2.3'),
                PyProjectInfo(
                    pyproject_toml_path=None,
                    raw_py_ver_req=None,
                    py_min_ver=Version('1.2.3'),
                ),
            )

            pyproject_toml = Path(temp_path, 'pyproject.toml')
            pyproject_toml.touch()
            self.assertEqual(
                get_pyproject_info(temp_path, default_min_py_version='3.8'),
                PyProjectInfo(
                    pyproject_toml_path=pyproject_toml,
                    raw_py_ver_req=None,
                    py_min_ver=Version('3.8'),
                ),
            )

            pyproject_toml.write_text(
                inspect.cleandoc(
                    '''
                    [project]
                    foo=1
                    requires-python = ">=3.10,<4"
                    bar=2
                    '''
                )
            )
            self.assertEqual(
                get_pyproject_info(temp_path, default_min_py_version='3.11'),
                PyProjectInfo(
                    pyproject_toml_path=pyproject_toml,
                    raw_py_ver_req='>=3.10,<4',
                    py_min_ver=Version('3.10'),
                ),
            )

            pyproject_toml.write_text(
                inspect.cleandoc(
                    """
                    [tool.poetry.dependencies]
                    foo=1
                    python = '>=3.11,<4.0.0'
                    bar=2
                    """
                )
            )
            self.assertEqual(
                get_pyproject_info(temp_path, default_min_py_version='3.8'),
                PyProjectInfo(
                    pyproject_toml_path=pyproject_toml,
                    raw_py_ver_req='>=3.11,<4.0.0',
                    py_min_ver=Version('3.11'),
                ),
            )

            pyproject_toml.write_text(
                inspect.cleandoc(
                    """
                    [project]
                    requires-python = ">=3.99,<4"
                    """
                )
            )
            self.assertEqual(
                get_pyproject_info(temp_path, default_min_py_version='3.11'),
                PyProjectInfo(
                    pyproject_toml_path=pyproject_toml,
                    raw_py_ver_req='>=3.99,<4',
                    py_min_ver=Version('3.11'),
                ),
            )

        self.assertEqual(
            get_pyproject_info(file_path=Path(__file__), default_min_py_version='3.7'),
            PyProjectInfo(
                pyproject_toml_path=PACKAGE_ROOT / 'pyproject.toml',
                py_min_ver=Version('3.11'),
                raw_py_ver_req='>=3.11',
            ),
        )

    def test_get_editorconfig_max_line_length(self):
        self.assertEqual(get_editorconfig_max_line_length(file_path=Path(__file__)), 119)
        with TemporaryDirectory(prefix='test_get_main_branch_name') as temp_path:
            self.assertIsNone(get_editorconfig_max_line_length(file_path=temp_path))

    def test_get_config(self):
        with AssertLogs(self, loggers=('cli_base',)):
            config = get_config(file_path=Path(__file__))
            self.assertIsInstance(config, Config)
            self.assertEqual(
                config,
                Config(
                    git_info=GitInfo(git=config.git_info.git, main_branch_name='main'),
                    pyproject_info=PyProjectInfo(
                        pyproject_toml_path=PACKAGE_ROOT / 'pyproject.toml',
                        py_min_ver=Version('3.11'),
                        raw_py_ver_req='>=3.11',
                    ),
                    max_line_length=119,
                ),
            )
            with TemporaryDirectory(prefix='test_get_config') as temp_path:
                config = get_config(file_path=temp_path)
                self.assertIsInstance(config, Config)
                self.assertEqual(
                    config,
                    Config(
                        git_info=None,
                        pyproject_info=PyProjectInfo(
                            py_min_ver=Version('3.10'), pyproject_toml_path=None, raw_py_ver_req=None
                        ),
                        max_line_length=119,
                    ),
                )

    def test_format_one_file(self):
        with (
            AssertLogs(self, loggers=('cli_base',)),
            SubprocessCallMock(
                return_callback=SimpleRunReturnCallback(
                    stdout='* main',  # "git branch" call -> bach name found -> use Darker
                )
            ) as call_mock,
        ):
            format_one_file(
                default_min_py_version='3.11',
                default_max_line_length=123,
                file_path=Path(__file__),
            )

        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(PY_BIN_PATH, GIT_BIN_PARENT)),
            [
                ['.../git', 'branch', '--no-color'],
                ['.../git', 'diff', 'origin/main', '--unified=0', 'manageprojects/tests/test_format_file.py'],
                ['.../ruff', 'format', '--target-version', 'py311', 'manageprojects/tests/test_format_file.py'],
                [
                    '.../ruff',
                    'check',
                    '--target-version',
                    'py311',
                    '--select',
                    'I001,F401',
                    '--fix',
                    '--unsafe-fixes',
                    'manageprojects/tests/test_format_file.py',
                ],
                ['.../ruff', 'check', '--target-version', 'py311', 'manageprojects/tests/test_format_file.py'],
                ['.../codespell', 'manageprojects/tests/test_format_file.py'],
                [
                    '.../mypy',
                    '--ignore-missing-imports',
                    '--follow-imports',
                    'skip',
                    '--allow-redefinition',
                    'manageprojects/tests/test_format_file.py',
                ],
            ],
        )

        with (
            AssertLogs(self, loggers=('cli_base',)),
            SubprocessCallMock(
                return_callback=SimpleRunReturnCallback(
                    stdout='',  # No git branch name found -> Format the complete file
                )
            ) as call_mock,
        ):
            format_one_file(
                default_min_py_version='3.11',
                default_max_line_length=123,
                file_path=Path(__file__),
            )

        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(PY_BIN_PATH, GIT_BIN_PARENT)),
            [
                ['.../git', 'branch', '--no-color'],
                ['.../ruff', 'format', '--target-version', 'py311', 'manageprojects/tests/test_format_file.py'],
                ['.../ruff', 'check', '--target-version', 'py311', 'manageprojects/tests/test_format_file.py'],
                ['.../codespell', 'manageprojects/tests/test_format_file.py'],
                [
                    '.../mypy',
                    '--ignore-missing-imports',
                    '--follow-imports',
                    'skip',
                    '--allow-redefinition',
                    'manageprojects/tests/test_format_file.py',
                ],
            ],
        )
