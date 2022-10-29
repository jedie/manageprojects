import filecmp
import inspect
import json
from pathlib import Path

import tomli
import yaml
from bx_py_utils.environ import OverrideEnviron
from bx_py_utils.path import assert_is_dir, assert_is_file

from manageprojects.cookiecutter_templates import run_cookiecutter, update_project
from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.patching import GenerateTemplatePatchResult
from manageprojects.tests.base import BaseTestCase
from manageprojects.tests.utilities.fixtures import copy_fixtures
from manageprojects.tests.utilities.git_utils import init_git
from manageprojects.utilities.pyproject_toml import PyProjectToml
from manageprojects.utilities.temp_path import TemporaryDirectory


class ManageProjectsTestCase(BaseTestCase):
    def test_run_cookiecutter(self):
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

            result: CookiecutterResult = run_cookiecutter(
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
            toml = PyProjectToml(project_path=project_path)
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "84d23bf"
                    initial_date = 2022-10-24T19:15:47+02:00
                    cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
                    cookiecutter_directory = "test_template1"

                    [manageprojects.cookiecutter_context]
                    dir_name = "a_dir_name"
                    file_name = "a_file_name"
                    '''
                ),
            )

    def test_start_project(self):
        with TemporaryDirectory(prefix='test_start_project_') as main_temp_path:

            cookiecutter_directory = 'cookiecutter_directory'
            template_path = main_temp_path / cookiecutter_directory
            template_file_path = (
                template_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )

            new_file_path = template_path / '{{cookiecutter.dir_name}}' / 'new_file.py'

            cookiecutter_destination = main_temp_path / 'cookiecutter_output_dir'
            project_path = cookiecutter_destination / 'default_directory_name'
            destination_file_path = project_path / 'default_file_name.py'
            pyproject_toml_path = project_path / 'pyproject.toml'

            #########################################################################
            # copy existing cookiecutter template to /tmp/:

            copy_fixtures(
                fixtures_dir_name='cookiecutter_simple_template_rev1',
                destination=template_path,
            )
            assert_is_file(template_file_path)

            #########################################################################
            # Make git repro and commit the current state:

            template_git, git_hash1 = init_git(template_path)
            self.assertEqual(len(git_hash1), 7)

            file_paths = template_git.ls_files(verbose=False)
            expected_paths = [
                Path(template_path / 'cookiecutter.json'),
                template_file_path,
            ]
            self.assertEqual(file_paths, expected_paths)

            #########################################################################
            # start project in /tmp/:

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

            replay_file_path = replay_dir_path / f'{cookiecutter_directory}.json'

            self.assertFalse(cookiecutter_destination.exists())
            self.assertFalse(cookiecutters_dir.exists())
            self.assertFalse(replay_file_path.exists())
            self.assertFalse(project_path.exists())

            from manageprojects.cli import start_project  # import loops

            result: CookiecutterResult = start_project(
                template=str(template_path),
                output_dir=cookiecutter_destination,
                no_input=True,
                # directory=cookiecutter_directory,
                config_file=config_file_path,
            )

            assert_is_dir(project_path)
            self.assertFalse(cookiecutters_dir.exists())  # no git clone, because local repo?
            assert_is_file(replay_file_path)

            self.assertIsInstance(result, CookiecutterResult)
            self.assertEqual(result.git_path, template_path)

            # Cookiecutter creates a replay JSON?
            assert_is_file(replay_file_path)
            replay_json = replay_file_path.read_text()
            replay_data = json.loads(replay_json)
            self.assertDictEqual(
                replay_data,
                {
                    'cookiecutter': {  # All template defaults:
                        'dir_name': 'default_directory_name',
                        'file_name': 'default_file_name',
                        'value': 'default_value',
                        '_template': str(template_path),
                        '_output_dir': str(cookiecutter_destination),
                    }
                },
            )

            # Check created file:
            assert_is_file(destination_file_path)
            filecmp.cmp(destination_file_path, template_file_path)

            # Check created toml file:
            toml = PyProjectToml(project_path=project_path)
            meta = toml.get_mp_meta()
            self.assertIsInstance(meta, ManageProjectsMeta)
            self.assertEqual(meta.initial_revision, git_hash1)
            self.assertEqual(meta.applied_migrations, [])
            self.assertEqual(meta.cookiecutter_template, str(template_path))
            self.assertEqual(meta.cookiecutter_directory, None)
            self.assert_datetime_now_range(meta.initial_date, max_diff_sec=5)

            # Create a git, with this state
            init_git(cookiecutter_destination, comment='Project start')

            #########################################################################
            # Change the source template and update the existing project

            # Add a new template file:
            new_file_path.write_text('print("This is a new added file in template rev2')
            template_git.add('.', verbose=False)
            template_git.commit('Add a new file', verbose=False)
            git_hash2 = template_git.get_current_hash(verbose=False)

            # Change a existing file:
            with template_file_path.open('a') as f:
                f.write('\n# This comment was added in rev2 ;)\n')
            template_git.add('.', verbose=False)
            template_git.commit('Update existing file', verbose=False)
            git_hash3 = template_git.get_current_hash(verbose=False)

            log_lines = template_git.log(format='%h - %s', verbose=False)
            self.assertEqual(
                log_lines,
                [
                    f'{git_hash3} - Update existing file',
                    f'{git_hash2} - Add a new file',
                    f'{git_hash1} - The initial commit ;)',
                ],
            )

            #########################################################################
            # update the existing project

            self.assert_file_content(destination_file_path, "print('Hello World: default_value')")

            pyproject_before = tomli.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
            self.assertDictEqual(
                pyproject_before,
                {
                    'manageprojects': {
                        'initial_revision': meta.initial_revision,
                        'initial_date': meta.initial_date,
                        'cookiecutter_template': str(template_path),
                        'cookiecutter_context': {
                            'dir_name': 'default_directory_name',
                            'file_name': 'default_file_name',
                            'value': 'default_value',
                        },
                    }
                },
            )

            with OverrideEnviron(XDG_CONFIG_HOME=str(main_temp_path)):
                update_result = update_project(
                    project_path=project_path, config_file=config_file_path
                )
            self.assertIsInstance(update_result, GenerateTemplatePatchResult)

            self.assert_file_content(
                destination_file_path,
                inspect.cleandoc(
                    '''
                    print('Hello World: default_value')

                    # This comment was added in rev2 ;)
                    '''
                ),
            )

            pyproject_after = tomli.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
            print(pyproject_after)
            self.assertDictEqual(
                pyproject_after,
                {
                    'manageprojects': {
                        'initial_revision': meta.initial_revision,
                        'initial_date': meta.initial_date,
                        'cookiecutter_template': str(template_path),
                        'cookiecutter_context': {
                            'dir_name': 'default_directory_name',
                            'file_name': 'default_file_name',
                            'value': 'default_value',
                        },
                    }
                },
            )
