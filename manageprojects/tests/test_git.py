import contextlib
import datetime
import io
from pathlib import Path
from unittest import TestCase

from bx_py_utils.test_utils.datetime import parse_dt

from manageprojects import __version__
from manageprojects.cli import PACKAGE_ROOT, version
from manageprojects.git import Git


class GitTestCase(TestCase):
    def test_basic(self):
        deep_path = Path(__file__).parent
        git = Git(cwd=deep_path)
        git_root_path = git.cwd
        self.assertNotEqual(git_root_path, deep_path)
        self.assertEqual(git_root_path, PACKAGE_ROOT)

        git_hash = git.get_current_hash(verbose=False)
        self.assertEqual(len(git_hash), 7, f'Wrong: {git_hash!r}')

        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            version()

        output = buffer.getvalue()
        self.assertEqual(output, f'manageprojects v{__version__} {git_hash}\n')

        commit_date = git.get_commit_date(verbose=False)
        self.assertIsInstance(commit_date, datetime.datetime)
        self.assertGreater(commit_date, parse_dt('2022-10-25T00:00:00+0000'))
        self.assertLess(commit_date, parse_dt('2023-01-01T00:00:00+0000'))  # ;)
