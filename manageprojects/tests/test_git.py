import contextlib
import datetime
import filecmp
import inspect
import io
import shutil
from pathlib import Path
from unittest import TestCase

from bx_py_utils.test_utils.datetime import parse_dt
from bx_py_utils.test_utils.snapshot import assert_text_snapshot

from manageprojects import __version__
from manageprojects.cli.cli_app import PACKAGE_ROOT, version
from manageprojects.git import Git
from manageprojects.test_utils.git_utils import init_git
from manageprojects.utilities.temp_path import TemporaryDirectory


class GitTestCase(TestCase):
    def test_config(self):
        with TemporaryDirectory(prefix='test_init_git_') as temp_path:
            git = Git(cwd=temp_path, detect_root=False)
            git.init()

            self.assertEqual(git.get_config(key='user.name'), 'manageprojects')
            self.assertEqual(git.get_config(key='user.email'), 'manageprojects@test.tld')

            keys = git.list_config_keys()
            self.assertIsInstance(keys, set)
            self.assertGreaterEqual(len(keys), 1)

            section = 'manageprojects'
            test_key = f'{section}.test-config-entry'

            value = git.get_config(key=test_key)
            self.assertIsNone(value)

            git.config(key=test_key, value='test', scope='local')
            value = git.get_config(key=test_key)
            self.assertEqual(value, 'test')

            git.git_verbose_check_output('config', '--local', '--remove-section', section)

            value = git.get_config(key=test_key)
            self.assertIsNone(value)

    def test_own_git_repo(self):
        deep_path = Path(__file__).parent
        git = Git(cwd=deep_path)
        git_root_path = git.cwd
        self.assertNotEqual(git_root_path, deep_path)
        self.assertEqual(git_root_path, PACKAGE_ROOT)

        git_hash = git.get_current_hash(verbose=False)
        self.assertEqual(len(git_hash), 7, f'Wrong: {git_hash!r}')

        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            version(no_color=True)

        output = buffer.getvalue()
        self.assertEqual(output, f'manageprojects v{__version__} {git_hash}\n')

        commit_date = git.get_commit_date(verbose=False)
        self.assertIsInstance(commit_date, datetime.datetime)
        self.assertGreater(commit_date, parse_dt('2022-10-25T00:00:00+0000'))
        self.assertLess(commit_date, parse_dt('2023-01-01T00:00:00+0000'))  # ;)

    def test_init_git(self):
        with TemporaryDirectory(prefix='test_init_git_') as temp_path:
            Path(temp_path, 'foo.txt').touch()
            Path(temp_path, 'bar.txt').touch()

            git, git_hash = init_git(temp_path)
            self.assertEqual(len(git_hash), 7)
            self.assertEqual(
                git.ls_files(verbose=False),
                [Path(temp_path, 'bar.txt'), Path(temp_path, 'foo.txt')],
            )

    def test_git_diff(self):
        with TemporaryDirectory(prefix='test_git_diff_') as temp_path:
            change_txt_path = Path(temp_path, 'change.txt')
            change_txt_path.write_text('This is the first revision!')
            Path(temp_path, 'unchange.txt').write_text('This file will be not changed')

            git, first_hash = init_git(temp_path)
            self.assertEqual(len(first_hash), 7)
            self.assertEqual(
                git.ls_files(verbose=False),
                [Path(temp_path, 'change.txt'), Path(temp_path, 'unchange.txt')],
            )

            change_txt_path.write_text('This is the second revision!')

            git.add('.', verbose=False)
            git.commit('The second commit', verbose=False)

            second_hash = git.get_current_hash(verbose=False)
            reflog = git.reflog(verbose=False)
            self.assertIn('The second commit', reflog)
            self.assertIn(first_hash, reflog)
            self.assertIn(second_hash, reflog)

            diff_txt = git.diff(first_hash, second_hash)
            self.assertIn('--- a/change.txt', diff_txt)
            self.assertIn('+++ b/change.txt', diff_txt)
            self.assertIn('@@ -1 +1 @@', diff_txt)
            assert_text_snapshot(got=diff_txt, extension='.patch')

    def test_git_apply_patch(self):
        with TemporaryDirectory(prefix='test_git_apply_patch_') as temp_path:
            repo_path = temp_path / 'git-repo'
            project_path = temp_path / 'project'

            repo_change_path = repo_path / 'directory1' / 'pyproject.toml'
            repo_change_path.parent.mkdir(parents=True)
            repo_change_path.write_text(
                inspect.cleandoc(
                    '''
                    [tool.darker]
                    src = ['.']
                    revision = "origin/main..."
                    line_length = 79  # 79 is initial, change to 100 later
                    verbose = true
                    diff = false
                    '''
                )
            )
            Path(repo_path, 'directory1', 'unchanged.txt').write_text('Will be not changed file')

            shutil.copytree(repo_path, project_path)  # "fake" cookiecutter output
            project_git, project_first_hash = init_git(project_path)  # init project

            # 1:1 copy?
            project_change_path = project_path / 'directory1' / 'pyproject.toml'
            self.assertTrue(filecmp.cmp(project_change_path, repo_change_path))

            # init "cookiecutter" source project:
            repo_git, repo_first_hash = init_git(repo_path)

            # Add a change to "fake" source:
            repo_change_path.write_text(
                inspect.cleandoc(
                    '''
                    [tool.darker]
                    src = ['.']
                    revision = "origin/main..."
                    line_length = 100  # 79 is initial, change to 100 later
                    verbose = true
                    diff = false
                    '''
                )
            )
            repo_git.add('.', verbose=False)
            repo_git.commit('The second commit', verbose=False)
            second_hash = repo_git.get_current_hash(verbose=False)

            # Generate a patch via git diff:
            diff_txt = repo_git.diff(repo_first_hash, second_hash)
            self.assertIn('directory1/pyproject.toml', diff_txt)
            patch_file_path = temp_path / 'git-diff-1.patch'
            patch_file_path.write_text(diff_txt)
            assert_text_snapshot(got=diff_txt, extension='.patch')

            # Change the project a little bit, before apply the git diff patch:

            # Just add a new file, unrelated to the diff patch:
            Path(project_path, 'directory1', 'new.txt').write_text('A new project file')

            # Commit the new file:
            project_git.add('.', verbose=False)
            project_git.commit('Add a new project file', verbose=False)

            # Change a diff related file:
            project_change_path.write_text(
                inspect.cleandoc(
                    '''
                    [tool.darker]
                    src = ['.']
                    revision = "origin/main..."
                    line_length = 79  # 79 is initial, change to 100 later
                    verbose = true
                    skip_string_normalization = true  # Added from project
                    diff = false
                    '''
                )
            )

            # Commit the changes, too:
            project_git.add('.', verbose=False)
            project_git.commit('Existing project file changed', verbose=False)

            # Now: Merge the project changes with the "fake" cookiecutter changes:
            project_git.apply(patch_file_path)

            # Merge successful?
            #  * line_length <<< change from "fake" cookiecutter changed
            #  * skip_string_normalization <<< added by project
            # The Rest is unchanged
            self.assertEqual(
                project_change_path.read_text(),
                inspect.cleandoc(
                    '''
                    [tool.darker]
                    src = ['.']
                    revision = "origin/main..."
                    line_length = 100  # 79 is initial, change to 100 later
                    verbose = true
                    skip_string_normalization = true  # Added from project
                    diff = false
                    '''
                ),
            )
