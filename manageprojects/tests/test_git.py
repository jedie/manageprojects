import datetime
import filecmp
import inspect
import shutil
from pathlib import Path
from unittest import TestCase

from bx_py_utils.test_utils.datetime import parse_dt
from bx_py_utils.test_utils.snapshot import assert_text_snapshot
from packaging.version import Version

from manageprojects.cli.cli_app import PACKAGE_ROOT
from manageprojects.git import Git, GitTagInfo, GitTagInfos
from manageprojects.test_utils.git_utils import init_git
from manageprojects.test_utils.logs import AssertLogs
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

        commit_date = git.get_commit_date(verbose=False)
        self.assertIsInstance(commit_date, datetime.datetime)
        self.assertGreater(commit_date, parse_dt('2023-01-01T00:00:00+0000'))
        self.assertLess(commit_date, parse_dt('2024-01-01T00:00:00+0000'))  # ;)

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

    def test_status(self):
        with TemporaryDirectory(prefix='test_status_') as temp_path:
            change_txt_path = Path(temp_path, 'change.txt')
            change_txt_path.write_text('This is the first revision!')

            git, first_hash = init_git(temp_path)

            change_txt_path.write_text('Changed content')
            Path(temp_path, 'added.txt').write_text('Added file')

            status = git.status(verbose=False)
            self.assertEqual(status, [('M', 'change.txt'), ('??', 'added.txt')])

            git.add('.', verbose=False)
            git.commit('The second commit', verbose=False)

            status = git.status(verbose=False)
            self.assertEqual(status, [])

    def test_branch_names(self):
        with TemporaryDirectory(prefix='test_branch_names_') as temp_path:
            Path(temp_path, 'foo.txt').touch()
            git, first_hash = init_git(temp_path)

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                branch_names = git.get_branch_names()
                self.assertEqual(branch_names, ['main'])
            logs.assert_in("Git raw branches: ['* main']")

            git.git_verbose_check_call('checkout', '-b', 'foobar')

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                branch_names = git.get_branch_names()
                self.assertEqual(branch_names, ['foobar', 'main'])
            logs.assert_in("Git raw branches: ['* foobar', '  main']")

            with AssertLogs(self, loggers=('manageprojects',)):
                main_branch_name = git.get_main_branch_name()
                self.assertEqual(main_branch_name, 'main')

    def test_log(self):
        with TemporaryDirectory(prefix='test_get_version_from_tags') as temp_path:
            Path(temp_path, '1.txt').touch()
            git, first_hash = init_git(temp_path, comment='The initial commit ;)')

            git.tag('v0.0.1', message='one', verbose=False)

            Path(temp_path, '2.txt').touch()
            git.add(spec='.')
            git.commit(comment='Useless 1')

            Path(temp_path, '3.txt').touch()
            git.add(spec='.')
            git.commit(comment='Useless 2')

            git.tag('v0.2.0', message='two', verbose=False)
            Path(temp_path, '4.txt').touch()
            git.add(spec='.')
            git.commit(comment='Useless 3')

            output = git.log(format='%s')
            self.assertEqual(output, ['Useless 3', 'Useless 2', 'Useless 1', 'The initial commit ;)'])

            output = git.log(format='%s', no_merges=True, commit1='HEAD', commit2='v0.0.1')
            self.assertEqual(output, ['Useless 3', 'Useless 2', 'Useless 1'])

    def test_get_version_from_tags(self):
        with TemporaryDirectory(prefix='test_get_version_from_tags') as temp_path:
            Path(temp_path, 'foo.txt').touch()
            git, first_hash = init_git(temp_path)

            empty_tags = git.get_tag_infos()
            self.assertEqual(empty_tags, GitTagInfos(tags=[]))
            self.assertEqual(empty_tags.get_releases(), [])
            self.assertIs(empty_tags.get_last_release(), None)

            git.tag('v0.0.1', message='one', verbose=False)
            git.tag('v0.2.dev1', message='dev release', verbose=False)
            git.tag('v0.2.0a1', message='pre release', verbose=False)
            git.tag('v0.2.0rc2', message='release candidate', verbose=False)
            git.tag('v0.2.0', message='two', verbose=False)
            git.tag('foo', message='foo', verbose=False)
            git.tag('bar', message='bar', verbose=False)

            self.assertEqual(git.tag_list(), ['bar', 'foo', 'v0.0.1', 'v0.2.0', 'v0.2.0a1', 'v0.2.0rc2', 'v0.2.dev1'])

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                git_tag_infos = git.get_tag_infos()
                self.assertEqual(
                    git_tag_infos,
                    GitTagInfos(
                        tags=[
                            GitTagInfo(raw_tag='bar', version=None),
                            GitTagInfo(raw_tag='foo', version=None),
                            GitTagInfo(raw_tag='v0.0.1', version=Version('0.0.1')),
                            GitTagInfo(raw_tag='v0.2.dev1', version=Version('0.2.dev1')),
                            GitTagInfo(raw_tag='v0.2.0a1', version=Version('0.2.0a1')),
                            GitTagInfo(raw_tag='v0.2.0rc2', version=Version('0.2.0rc2')),
                            GitTagInfo(raw_tag='v0.2.0', version=Version('0.2.0')),
                        ]
                    ),
                )
            logs.assert_in('Ignore: Invalid version')

            self.assertTrue(git_tag_infos.exists(Version('0.0.1')))
            self.assertTrue(git_tag_infos.exists(Version('0.2.0rc2')))
            self.assertFalse(git_tag_infos.exists(Version('1.0')))

            self.assertEqual(
                git_tag_infos.get_releases(),
                [
                    GitTagInfo(raw_tag='v0.0.1', version=Version('0.0.1')),
                    GitTagInfo(raw_tag='v0.2.0', version=Version('0.2.0')),
                ],
            )
            self.assertEqual(
                git_tag_infos.get_last_release(),
                GitTagInfo(raw_tag='v0.2.0', version=Version('0.2.0')),
            )
