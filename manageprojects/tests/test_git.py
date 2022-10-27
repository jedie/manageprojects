import contextlib
import datetime
import io
from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_dir, assert_is_file
from bx_py_utils.test_utils.datetime import parse_dt

from manageprojects import __version__
from manageprojects.cli import PACKAGE_ROOT, version
from manageprojects.git import Git
from manageprojects.tests.utilities.fixtures import copy_fixtures
from manageprojects.tests.utilities.git_utils import init_git
from manageprojects.tests.utilities.temp_utils import TemporaryDirectory


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

    def test_init_git(self):
        with TemporaryDirectory(prefix='ttest_init_git_') as temp_path:
            Path(temp_path, 'foo.txt').touch()
            Path(temp_path, 'bar.txt').touch()

            git, git_hash = init_git(temp_path)
            self.assertEqual(len(git_hash), 7)
            self.assertEqual(
                git.ls_files(verbose=False),
                [Path(temp_path, 'bar.txt'), Path(temp_path, 'foo.txt')],
            )

    def test_create_cookiecutter_template(self):
        with TemporaryDirectory(prefix='test_create_cookiecutter_template_') as temp_path:

            template_path = copy_fixtures(
                fixtures_dir_name='cookiecutter_simple_template_rev1',
                temp_path=temp_path,
                dst_dir_name='test-template',
            )

            self.assertEqual(template_path, temp_path / 'test-template')
            assert_is_dir(template_path)
            assert_is_file(
                template_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )

            git, git_hash = init_git(temp_path)
            self.assertEqual(len(git_hash), 7)

            file_paths = git.ls_files(verbose=False)
            expected_paths = [
                Path(template_path / 'cookiecutter.json'),
                Path(template_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'),
            ]
            self.assertEqual(file_paths, expected_paths)
