import inspect
import json
from pathlib import Path

from manageprojects.cookiecutter_templates import update_project
from manageprojects.patching import GenerateTemplatePatchResult
from manageprojects.tests.base import BaseTestCase
from manageprojects.tests.utilities.git_utils import init_git
from manageprojects.utilities.pyproject_toml import PyProjectToml
from manageprojects.utilities.temp_path import TemporaryDirectory


class CookiecutterTemplatesTestCase(BaseTestCase):
    def test_update_project(self):
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
        cookiecutter_context = {
            'dir_name': 'a_directory',
            'file_name': 'a_file_name',
            'value': 'FooBar',
        }
        context = {'cookiecutter': cookiecutter_context}

        with TemporaryDirectory(prefix='test_generate_template_patch_') as main_temp_path:
            project_path = main_temp_path / 'main_temp_path'
            dst_file_path = project_path / 'a_directory' / 'a_file_name.py'

            template_path = main_temp_path / 'template'
            template_dir_name = 'template_dir'
            template_dir_path = template_path / template_dir_name
            config_file_path = template_dir_path / 'cookiecutter.json'

            test_file_path = (
                template_dir_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )

            dst_file_path.parent.mkdir(parents=True)
            dst_file_path.write_text('# This is a test line, not changed')

            config_file_path.parent.mkdir(parents=True)
            config_file_path.write_text(json.dumps(cookiecutter_context))

            init_git(project_path, comment='Git init project.')

            test_file_path.parent.mkdir(parents=True)
            test_file_path.write_text(rev1_content)

            git, from_rev = init_git(template_path, comment='Git init template.')
            from_date = git.get_commit_date(verbose=False)

            toml = PyProjectToml(project_path=project_path)
            toml.init(
                revision=from_rev,
                dt=from_date,
                template=str(template_path),
                directory=template_dir_name,
            )
            toml.create_or_update_cookiecutter_context(context=context)
            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    f'''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "{from_rev}"
                    initial_date = {from_date.isoformat()}
                    cookiecutter_template = "{template_path}"
                    cookiecutter_directory = "template_dir"

                    [manageprojects.cookiecutter_context.cookiecutter]
                    dir_name = "a_directory"
                    file_name = "a_file_name"
                    value = "FooBar"
                    '''
                ),
            )

            test_file_path.write_text(rev2_content)
            git.add('.', verbose=False)
            git.commit('Template rev 2', verbose=False)
            to_rev = git.get_current_hash(verbose=False)
            to_date = git.get_commit_date(verbose=False)
            assert to_date

            patch_file_path = Path(
                main_temp_path,
                'repo_path',
                '.manageprojects',
                'patches',
                f'{from_rev}_{to_rev}.patch',
            )
            self.assertFalse(patch_file_path.exists())

            result = update_project(
                project_path=project_path,
                password=None,
                config_file=config_file_path,
                cleanup=False,  # Remove temp files if not exceptions happens
            )
            self.assertIsInstance(result, GenerateTemplatePatchResult)
            self.assertEqual(result, 123)
