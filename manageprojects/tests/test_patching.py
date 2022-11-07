import inspect
import json
from pathlib import Path

from bx_py_utils.path import assert_is_dir

from manageprojects.data_classes import GenerateTemplatePatchResult
from manageprojects.patching import generate_template_patch
from manageprojects.tests.base import BaseTestCase
from manageprojects.tests.utilities.git_utils import init_git
from manageprojects.utilities.temp_path import TemporaryDirectory


class PatchingTestCase(BaseTestCase):
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

            result = generate_template_patch(
                project_path=project_path,
                template=str(repo_path),
                directory=None,
                from_rev=from_rev,
                replay_context={},
                cleanup=False,  # Keep temp files if this test fails, for better debugging
                no_input=True,  # No user input in tests ;)
            )
            self.assertIsInstance(result, GenerateTemplatePatchResult)

            self.assertEqual(result.patch_file_path, patch_file_path)
            self.assertEqual(result.from_rev, from_rev)
            self.assertEqual(result.to_rev, to_rev)
            self.assertEqual(result.to_commit_date, to_date)

            self.assert_file_content(
                patch_file_path,
                inspect.cleandoc(
                    r'''
                    diff --git a/a_directory/a_file_name.py b/a_directory/a_file_name.py
                    index 4d0e75c..c71c9fe 100644
                    --- a/a_directory/a_file_name.py
                    +++ b/a_directory/a_file_name.py
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
