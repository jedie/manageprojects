from pathlib import Path
from unittest import TestCase

from packaging.version import Version

from manageprojects.test_utils.git_utils import init_git
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.test_utils.subprocess import FakeStdout, SubprocessCallMock
from manageprojects.tests.base import GIT_BIN_PARENT
from manageprojects.utilities.publish import PublisherGit
from manageprojects.utilities.temp_path import TemporaryDirectory


class PublishTestCase(TestCase):
    def test_publisher_git(self):
        with AssertLogs(self, loggers=('manageprojects',)), TemporaryDirectory(
            prefix='test_publisher_git'
        ) as temp_path:
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
            self.assertIs(pgit.change_msg, None)
            pgit.fast_checks()
            self.assertEqual(pgit.change_msg, ' * New commit 2\n * New commit 1')

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
                        'publish version v0.3.0 with these changes:\n\n * New commit 2\n * New commit 1\n',
                    ],
                    ['.../git', 'push', '--tags'],
                ],
            )
