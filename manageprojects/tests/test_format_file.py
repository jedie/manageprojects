import inspect
from pathlib import Path
from unittest import TestCase

from packaging.version import Version

from manageprojects.format_file import (
    Config,
    GitInfo,
    PyProjectInfo,
    format_one_file,
    get_config,
    get_editorconfig_max_line_length,
    get_git_info,
    get_pyproject_info,
)
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.test_utils.subprocess import SubprocessCallMock
from manageprojects.tests.base import PROJECT_PATH
from manageprojects.utilities.temp_path import TemporaryDirectory


class FormatFileTestCase(TestCase):
    def test_get_git_info(self):
        with AssertLogs(self, loggers=('manageprojects',)):
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
                    '''
                    [tool.poetry.dependencies]
                    foo=1
                    python = '>=3.11,<4.0.0'
                    bar=2
                    '''
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
                    '''
                    [project]
                    requires-python = ">=3.99,<4"
                    '''
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
                pyproject_toml_path=PROJECT_PATH / 'pyproject.toml',
                py_min_ver=Version('3.9'),
                raw_py_ver_req='>=3.9,<4',
            ),
        )

    def test_get_editorconfig_max_line_length(self):
        self.assertEqual(get_editorconfig_max_line_length(file_path=Path(__file__)), 119)
        with TemporaryDirectory(prefix='test_get_main_branch_name') as temp_path:
            self.assertIsNone(get_editorconfig_max_line_length(file_path=temp_path))

    def test_get_config(self):
        with AssertLogs(self, loggers=('manageprojects',)):
            config = get_config(file_path=Path(__file__))
            self.assertIsInstance(config, Config)
            self.assertEqual(
                config,
                Config(
                    git_info=GitInfo(cwd=PROJECT_PATH, main_branch_name='main'),
                    pyproject_info=PyProjectInfo(
                        pyproject_toml_path=PROJECT_PATH / 'pyproject.toml',
                        py_min_ver=Version('3.9'),
                        raw_py_ver_req='>=3.9,<4',
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
                            py_min_ver=Version('3.9'), pyproject_toml_path=None, raw_py_ver_req=None
                        ),
                        max_line_length=119,
                    ),
                )

    def test_format_one_file(self):
        with AssertLogs(self, loggers=('manageprojects',)), SubprocessCallMock() as call_mock:
            format_one_file(
                default_min_py_version='3.11',
                default_max_line_length=123,
                darker_prefixes='E456,E789',
                file_path=Path(__file__),
            )

        self.assertEqual(
            call_mock.get_popenargs(rstrip_path=PROJECT_PATH),
            [
                [
                    '.../.venv/bin/pyupgrade',
                    '--exit-zero-even-if-changed',
                    '--py39-plus',
                    'manageprojects/tests/test_format_file.py',
                ],
                [
                    '.../.venv/bin/autopep8',
                    '--ignore-local-config',
                    '--select',
                    'E456,E789',
                    '--max-line-length=119',
                    '--in-place',
                    'manageprojects/tests/test_format_file.py',
                ],
                [
                    '.../.venv/bin/darker',
                    '--flynt',
                    '--isort',
                    '--skip-string-normalization',
                    '--revision',
                    'main...',
                    '--line-length',
                    '119',
                    '--target-version',
                    'py39',
                    'manageprojects/tests/test_format_file.py',
                ],
                ['.../.venv/bin/flake8', '--max-line-length', '119', 'manageprojects/tests/test_format_file.py'],
                ['.../.venv/bin/pyflakes', 'manageprojects/tests/test_format_file.py'],
                ['.../.venv/bin/codespell', 'manageprojects/tests/test_format_file.py'],
                [
                    '.../.venv/bin/mypy',
                    '--ignore-missing-imports',
                    '--follow-imports',
                    'skip',
                    '--allow-redefinition',
                    'manageprojects/tests/test_format_file.py',
                ],
            ],
        )
