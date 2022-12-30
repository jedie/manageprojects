import inspect
import json
from pathlib import Path

import yaml
from bx_py_utils.path import assert_is_dir, assert_is_file
from bx_py_utils.test_utils.datetime import parse_dt

from manageprojects.cli.cli_app import clone_project
from manageprojects.cookiecutter_templates import start_managed_project, update_managed_project
from manageprojects.data_classes import (
    CookiecutterResult,
    GenerateTemplatePatchResult,
    ManageProjectsMeta,
)
from manageprojects.test_utils.git_utils import init_git
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.pyproject_toml import PyProjectToml
from manageprojects.utilities.temp_path import TemporaryDirectory


class CookiecutterTemplatesTestCase(BaseTestCase):
    def test_start_managed_project(self):
        repro_name = 'mp_test_template1'
        cookiecutter_template = f'https://github.com/jedie/{repro_name}/'
        directory = 'test_template1'

        with TemporaryDirectory(prefix='manageprojects_') as main_temp_path:
            replay_dir_path = main_temp_path / '.cookiecutter_replay'
            replay_dir_path.mkdir()

            cookiecutters_dir = main_temp_path / '.cookiecutters'
            config = {
                'cookiecutters_dir': str(cookiecutters_dir),
                'replay_dir': str(replay_dir_path),
            }
            config_yaml = yaml.dump(config)
            config_file_path = main_temp_path / 'cookiecutter_config.yaml'
            config_file_path.write_text(config_yaml)

            replay_file_path = replay_dir_path / f'{directory}.json'
            cookiecutter_output_dir = main_temp_path / 'cookiecutter_output_dir'
            assert replay_file_path.exists() is False
            assert cookiecutter_output_dir.exists() is False
            assert cookiecutters_dir.exists() is False

            with AssertLogs(self) as logs:
                result: CookiecutterResult = start_managed_project(
                    template=cookiecutter_template,
                    output_dir=cookiecutter_output_dir,
                    no_input=True,
                    directory=directory,
                    config_file=config_file_path,
                    extra_context={
                        'dir_name': 'a_dir_name',
                        'file_name': 'a_file_name',
                    },
                )
            logs.assert_in('Cookiecutter generated here', cookiecutter_output_dir)

            self.assertIsInstance(result, CookiecutterResult)
            git_path = cookiecutters_dir / repro_name
            self.assertEqual(result.git_path, git_path)
            assert_is_dir(git_path)  # Checkout was made?
            assert_is_dir(cookiecutter_output_dir)  # Created from cookiecutter ?

            # Cookiecutter creates a replay JSON?
            assert_is_file(replay_file_path)
            replay_json = replay_file_path.read_text()
            replay_data = json.loads(replay_json)
            assert replay_data == {
                'cookiecutter': {
                    'dir_name': 'a_dir_name',
                    'file_name': 'a_file_name',
                    '_template': cookiecutter_template,
                    '_output_dir': str(cookiecutter_output_dir),
                }
            }

            # Our replay config was used?
            assert_is_file(cookiecutter_output_dir / 'a_dir_name' / 'a_file_name.py')

            project_path = cookiecutter_output_dir / 'a_dir_name'

            # pyproject.toml created?
            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=project_path)
                result: ManageProjectsMeta = toml.get_mp_meta()
            logs.assert_in('Read existing pyproject.toml')
            self.assertIsInstance(result, ManageProjectsMeta)
            self.assertEqual(
                result,
                ManageProjectsMeta(
                    initial_revision='42f18f3',
                    initial_date=parse_dt('2022-11-02T19:40:09+01:00'),
                    applied_migrations=[],
                    cookiecutter_template='https://github.com/jedie/mp_test_template1/',
                    cookiecutter_directory='test_template1',
                    cookiecutter_context={
                        'cookiecutter': {
                            'dir_name': 'a_dir_name',
                            'file_name': 'a_file_name',
                            '_template': 'https://github.com/jedie/mp_test_template1/',
                        }
                    },
                ),
            )

            ###################################################################################
            # Test clone a existing project

            cloned_path = main_temp_path / 'cloned_project'
            with AssertLogs(self) as logs:
                clone_result: CookiecutterResult = clone_project(
                    project_path=project_path, destination=cloned_path, no_input=True
                )
            logs.assert_in(
                'Read existing pyproject.toml',
                "Call 'cookiecutter'",
                'Create new pyproject.toml',
            )
            self.assertEqual(
                clone_result.cookiecutter_context,
                {
                    'cookiecutter': {
                        '_template': 'https://github.com/jedie/mp_test_template1/',
                        'dir_name': 'a_dir_name',
                        'file_name': 'a_file_name',
                    }
                },
            )
            end_path = cloned_path / 'a_dir_name'
            assert_is_dir(end_path)
            self.assertEqual(clone_result.destination_path, end_path)

            # pyproject.toml created?
            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=end_path)
                result: ManageProjectsMeta = toml.get_mp_meta()
            logs.assert_in('Read existing pyproject.toml')
            self.assertIsInstance(result, ManageProjectsMeta)
            self.assertEqual(
                result,
                ManageProjectsMeta(
                    initial_revision='42f18f3',
                    initial_date=parse_dt('2022-11-02T19:40:09+01:00'),
                    applied_migrations=[],
                    cookiecutter_template='https://github.com/jedie/mp_test_template1/',
                    cookiecutter_directory='test_template1',
                    cookiecutter_context={
                        'cookiecutter': {
                            'dir_name': 'a_dir_name',
                            'file_name': 'a_file_name',
                            '_template': 'https://github.com/jedie/mp_test_template1/',
                        }
                    },
                ),
            )

    def test_update_project(self):
        cookiecutter_context = {
            'dir_name': 'a_directory',
            'file_name': 'a_file_name',
            'value': 'FooBar',
        }
        context = {'cookiecutter': cookiecutter_context}

        with TemporaryDirectory(prefix='test_generate_template_patch_') as main_temp_path:
            project_path = main_temp_path / 'project_path'
            dst_file_path = project_path / 'a_file_name.py'

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

            project_git, project_from_rev = init_git(project_path, comment='Git init project.')
            dst_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 1
                    #
                    # The same cookiecutter value:
                    print('Test: FooBar')
                    '''
                )
            )
            project_git.add('.')
            project_git.commit('Store revision 1')

            test_file_path.parent.mkdir(parents=True)
            test_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 1
                    #
                    # The same cookiecutter value:
                    print('Test: {{ cookiecutter.value }}')
                    '''
                )
            )

            git, from_rev = init_git(template_path, comment='Git init template.')
            from_date = git.get_commit_date(verbose=False)

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=project_path)
                toml.init(
                    revision=from_rev,
                    dt=from_date,
                    template=str(template_path),
                    directory=template_dir_name,
                )
            logs.assert_in('Create new pyproject.toml')
            toml.create_or_update_cookiecutter_context(context=context)
            toml.save()
            toml_content = toml.path.read_text()
            self.assertIn('# Created by manageprojects', toml_content)
            self.assertIn(
                '[manageprojects] # https://github.com/jedie/manageprojects', toml_content
            )
            self.assertIn(f'initial_revision = "{from_rev}"', toml_content)
            self.assertIn(f'cookiecutter_template = "{template_path}"', toml_content)
            self.assertIn('cookiecutter_directory = "template_dir"', toml_content)

            test_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 2
                    #
                    # The same cookiecutter value:
                    print('Test: {{ cookiecutter.value }}')
                    '''
                )
            )
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

            with AssertLogs(self) as logs:
                result = update_managed_project(
                    project_path=project_path,
                    password=None,
                    config_file=config_file_path,
                    cleanup=False,  # Keep temp files if this test fails, for better debugging
                    no_input=True,  # No user input in tests ;)
                )
            logs.assert_in(
                'No temp files cleanup',
                'Cookiecutter generated',
                'Read existing pyproject.toml',
            )

            self.assert_file_content(
                dst_file_path,
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 2
                    #
                    # The same cookiecutter value:
                    print('Test: FooBar')
                    '''
                ),
            )

            self.assertIsInstance(result, GenerateTemplatePatchResult)
            patch_file_path = Path(
                project_path,
                '.manageprojects',
                'patches',
                f'{result.from_rev}_{result.to_rev}.patch',
            )
            assert_is_file(patch_file_path)
            patch_temp_path = result.compiled_to_path.parent
            self.assertEqual(
                result,
                GenerateTemplatePatchResult(
                    repo_path=template_dir_path,
                    patch_file_path=patch_file_path,
                    from_rev=from_rev,
                    compiled_from_path=patch_temp_path / f'{result.from_rev}_compiled',
                    to_rev=to_rev,
                    to_commit_date=to_date,
                    compiled_to_path=patch_temp_path / 'to_rev_compiled',
                ),
            )

            # Check updated toml file:
            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=project_path)
                mp_meta: ManageProjectsMeta = toml.get_mp_meta()
            logs.assert_in('Read existing pyproject.toml')
            self.assertEqual(mp_meta.initial_revision, from_rev)
            self.assertEqual(mp_meta.applied_migrations, [to_rev])
