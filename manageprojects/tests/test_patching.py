import inspect
import json
from pathlib import Path

from bx_py_utils.path import assert_is_dir
from bx_py_utils.test_utils.snapshot import assert_text_snapshot

from manageprojects.data_classes import GenerateTemplatePatchResult
from manageprojects.patching import generate_template_patch, make_git_diff
from manageprojects.test_utils.git_utils import init_git
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.temp_path import TemporaryDirectory


class PatchingTestCase(BaseTestCase):
    def test_make_git_diff(self):
        with TemporaryDirectory(prefix='test_make_git_diff_') as main_temp_path:
            from_path = main_temp_path / 'from'
            to_path = main_temp_path / 'to'

            from_path.mkdir()
            to_path.mkdir()

            Path(from_path, 'file1.txt').write_text('Rev 1')
            Path(to_path, 'file1.txt').write_text('Rev 2')

            renamed_file_content = inspect.cleandoc(
                '''
                # This file is just renamed,
                # so the content is the same ;)
                '''
            )
            Path(from_path, 'old_name.txt').write_text(renamed_file_content)
            Path(to_path, 'new_name.txt').write_text(renamed_file_content)

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                patch = make_git_diff(
                    temp_path=main_temp_path,
                    from_path=from_path,
                    to_path=to_path,
                    verbose=True,
                )
            logs.assert_in('old_name.txt', 'new_name.txt')
            self.assertIn('diff --git a/file1.txt b/file1.txt', patch)
            self.assertIn('-Rev 1', patch)
            self.assertIn('+Rev 2', patch)
            self.assertIn('rename from old_name.txt', patch)
            self.assertIn('rename to new_name.txt', patch)
            assert_text_snapshot(got=patch, extension='.patch')

    def test_generate_template_patch(self):
        rev1_content = inspect.cleandoc(
            '''
            # This is a test line, not changed
            #
            # Revision 1
            #
            # The same cookiecutter value:
            print('Test: {{ cookiecutter.value }}')
            '''
        )
        rev2_content = inspect.cleandoc(
            '''
            # This is a test line, not changed
            #
            # Revision 2
            #
            # The same cookiecutter value:
            print('Test: {{ cookiecutter.value }}')
            '''
        )

        with TemporaryDirectory(prefix='test_generate_template_patch_') as main_temp_path:
            project_path = main_temp_path / 'main_temp_path'
            repo_path = main_temp_path / 'repo_path'

            test_file_path = (
                repo_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )
            test_file_path.parent.mkdir(parents=True)
            test_file_path.write_text(rev1_content)
            cookiecutter_json_path = repo_path / 'cookiecutter.json'
            cookiecutter_json_path.write_text(
                json.dumps(
                    {
                        'dir_name': 'a_directory',
                        'file_name': 'a_file_name',
                        'value': 'FooBar',
                    }
                )
            )

            git, from_rev = init_git(repo_path)

            test_file_path.write_text(rev2_content)
            git.add('.', verbose=False)
            git.commit('The second commit', verbose=False)
            to_rev = git.get_current_hash(verbose=False)
            to_date = git.get_commit_date(verbose=False)

            patch_file_path = Path(
                project_path,
                '.manageprojects',
                'patches',
                f'{from_rev}_{to_rev}.patch',
            )
            self.assertFalse(patch_file_path.exists())

            with AssertLogs(self) as logs:
                result = generate_template_patch(
                    project_path=project_path,
                    template=str(repo_path),
                    directory=None,
                    from_rev=from_rev,
                    replay_context={},
                    cleanup=False,  # Keep temp files if this test fails, for better debugging
                    no_input=True,  # No user input in tests ;)
                )
            logs.assert_in("Call 'cookiecutter'", 'Write patch file')
            self.assertIsInstance(result, GenerateTemplatePatchResult)

            self.assertEqual(result.patch_file_path, patch_file_path)
            self.assertEqual(result.from_rev, from_rev)
            self.assertEqual(result.to_rev, to_rev)
            self.assertEqual(result.to_commit_date, to_date)

            self.assert_file_content(
                patch_file_path,
                inspect.cleandoc(
                    r'''
                    diff --git a/a_file_name.py b/a_file_name.py
                    index 4d0e75c..c71c9fe 100644
                    --- a/a_file_name.py
                    +++ b/a_file_name.py
                    @@ -1,6 +1,6 @@
                     # This is a test line, not changed
                     #
                    -# Revision 1
                    +# Revision 2
                     #
                     # The same cookiecutter value:
                     print('Test: FooBar')
                    \ No newline at end of file
                    '''
                ),
            )

            # The repro path contains the "from" revision:
            assert_is_dir(result.repo_path)
            self.assert_file_content(
                Path(
                    result.repo_path,
                    '{{cookiecutter.dir_name}}',
                    '{{cookiecutter.file_name}}.py',
                ),
                rev1_content,
            )
