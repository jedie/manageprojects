from pathlib import Path
from unittest import TestCase

from bx_py_utils.test_utils.redirect import RedirectOut

import manageprojects
from manageprojects import __version__
from manageprojects.cli.cli_app import PACKAGE_ROOT
from manageprojects.git import Git
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.utilities.temp_path import TemporaryDirectory
from manageprojects.utilities.version_info import print_version


class VersionInfoTestCase(TestCase):
    maxDiff = None

    def test_temp_content_file(self):
        git = Git(cwd=PACKAGE_ROOT)
        git_hash = git.get_current_hash(verbose=False)

        with RedirectOut() as buffer:
            print_version(module=manageprojects)

        self.assertEqual(buffer.stderr, '')
        self.assertEqual(buffer.stdout, f'manageprojects v{__version__} {git_hash} ({PACKAGE_ROOT})\n')

    def test_no_git(self):
        with RedirectOut() as buffer:
            print_version(module=manageprojects, project_root=Path('foo', 'bar'))

        self.assertEqual(buffer.stderr, '')
        self.assertEqual(buffer.stdout, f'manageprojects v{__version__} (No git found for: foo/bar)\n')

        with TemporaryDirectory(prefix='test_no_git') as temp_path:
            non_git_path = temp_path / '.git'
            non_git_path.mkdir()

            with AssertLogs(self, loggers=('manageprojects',)) as logs, RedirectOut() as buffer:
                print_version(module=manageprojects, project_root=temp_path)

            self.assertEqual(buffer.stderr, '')
            self.assertIn(f'manageprojects v{__version__} ', buffer.stdout)

            logs.assert_in('Error print version', 'Traceback')
