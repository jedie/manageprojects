import inspect
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from cli_base.cli_tools import subprocess_utils
from cli_base.cli_tools.test_utils.git_utils import init_git
from packaging.version import Version

import manageprojects
from manageprojects.cli.dev import PACKAGE_ROOT
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.test_utils.subprocess import FakeStdout, SubprocessCallMock
from manageprojects.tests.base import GIT_BIN_PARENT
from manageprojects.utilities.publish import (
    PublisherGit,
    build,
    clean_version,
    get_pyproject_toml_version,
    setuptools_dynamic_version,
)
from manageprojects.utilities.temp_path import TemporaryDirectory


try:
    import tomllib  # New in Python 3.11
except ImportError:
    import tomli as tomllib


class PublishTestCase(TestCase):
    def test_build(self):
        def return_callback(popenargs, args, kwargs):
            return FakeStdout(stdout='Mocked run output')

        with TemporaryDirectory(prefix='test_build') as temp_path, SubprocessCallMock(return_callback) as call_mock:
            build(package_path=temp_path)

        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(str(Path(sys.executable).parent),)),
            [
                ['.../python', '-m', 'build'],
            ],
        )

        # Use poetry:

        def prepare_popenargs_mock(popenargs, cwd=None):
            return popenargs, cwd

        def make_relative_path_mock(path, **kwargs):
            return path

        with TemporaryDirectory(prefix='test_build') as temp_path, SubprocessCallMock(
            return_callback
        ) as call_mock, patch.object(subprocess_utils, 'prepare_popenargs', prepare_popenargs_mock), patch.object(
            subprocess_utils, 'make_relative_path', make_relative_path_mock
        ):
            Path(temp_path / 'poetry.lock').touch()

            build(package_path=temp_path)

        self.assertEqual(
            call_mock.get_popenargs(),
            [
                ['poetry', 'build'],
            ],
        )

    def setuptools_dynamic_version(self):
        pyproject_toml_path = PACKAGE_ROOT / 'pyproject.toml'
        pyproject_toml = tomllib.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
        setuptools_version = setuptools_dynamic_version(
            pyproject_toml=pyproject_toml,
            pyproject_toml_path=pyproject_toml_path,
        )
        self.assertIsNotNone(setuptools_version)
        real_version = clean_version(manageprojects.__version__)
        self.assertEqual(setuptools_version, real_version)

    def test_get_pyproject_toml_version(self):
        with TemporaryDirectory(prefix='test_get_pyproject_toml_version') as temp_path:
            pyproject_toml_path = temp_path / 'pyproject.toml'
            pyproject_toml_path.touch()

            version = get_pyproject_toml_version(temp_path)
            self.assertIs(version, None)

            pyproject_toml_path.write_text(
                inspect.cleandoc(
                    '''
                    [project]
                    name = "foo"
                    version = "1.2"
                    description = "bar"
                    '''
                )
            )
            version = get_pyproject_toml_version(temp_path)
            self.assertEqual(version, Version('1.2'))

            pyproject_toml_path.write_text(
                inspect.cleandoc(
                    '''
                    [tool.poetry]
                    name = "foo"
                    version = "2.3"
                    description = "bar"
                    '''
                )
            )
            version = get_pyproject_toml_version(temp_path)
            self.assertEqual(version, Version('2.3'))

    def test_publisher_fast_checks_not_existing_tag(self):
        # https://github.com/jedie/manageprojects/issues/68
        with AssertLogs(self, loggers=('cli_base',)), TemporaryDirectory(
            prefix='test_publisher_fast_checks_not_existing_tag'
        ) as temp_path:
            Path(temp_path, '1.txt').touch()
            init_git(temp_path, comment='The initial commit ;)')

            pgit = PublisherGit(
                package_path=temp_path,
                version=Version('0.0.1'),
                possible_branch_names=('main',),
                tag_msg_log_format='%s',
            )
            self.assertIs(pgit.git_tag_msg, None)
            pgit.fast_checks()
            self.assertEqual(
                pgit.git_tag_msg,
                'publish version v0.0.1 with these changes:\n\n * The initial commit ;)\n',
            )

    def test_publisher_git(self):
        with AssertLogs(self, loggers=('cli_base',)), TemporaryDirectory(prefix='test_publisher_git') as temp_path:
            Path(temp_path, '1.txt').touch()
            git, first_hash = init_git(temp_path, comment='The initial commit ;)')

            git.tag('v0.0.1', message='one', verbose=False)

            Path(temp_path, '2.txt').touch()
            git.add(spec='.')
            git.commit(comment='Useless 1')

            git.tag('v0.2.0', message='two', verbose=False)

            Path(temp_path, '3.txt').touch()
            git.add(spec='.')
            git.commit(comment='New commit 1')

            Path(temp_path, '4.txt').touch()
            git.add(spec='.')
            git.commit(comment='New commit 2')

            pgit = PublisherGit(
                package_path=temp_path,
                version=Version('0.3.0'),
                possible_branch_names=('main',),
                tag_msg_log_format='%s',
            )
            self.assertIs(pgit.git_tag_msg, None)
            pgit.fast_checks()
            self.assertEqual(
                pgit.git_tag_msg,
                'publish version v0.3.0 with these changes (since v0.2.0):\n\n * New commit 2\n * New commit 1\n',
            )

            def return_callback(popenargs, args, kwargs):
                git_command = popenargs[1]
                if git_command == 'fetch':
                    return
                elif git_command == 'log':
                    return FakeStdout(stdout='')
                elif git_command == 'push':
                    return FakeStdout(stdout='Everything up-to-date')

            with SubprocessCallMock(return_callback) as call_mock:
                pgit.slow_checks()

            self.assertEqual(
                call_mock.get_popenargs(rstrip_paths=(GIT_BIN_PARENT,)),
                [
                    ['.../git', 'fetch', 'origin'],
                    ['.../git', 'log', 'HEAD..origin/main', '--oneline'],
                    ['.../git', 'push', 'origin', 'main'],
                ],
            )

            with SubprocessCallMock() as call_mock:
                pgit.finalize()

            self.assertEqual(
                call_mock.get_popenargs(rstrip_paths=(GIT_BIN_PARENT,)),
                [
                    [
                        '.../git',
                        'tag',
                        '-a',
                        'v0.3.0',
                        '-m',
                        (
                            'publish version v0.3.0 with these changes (since v0.2.0):'
                            '\n\n * New commit 2\n * New commit 1\n'
                        ),
                    ],
                    ['.../git', 'push', '--tags'],
                ],
            )
