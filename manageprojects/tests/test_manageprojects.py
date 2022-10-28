import filecmp
import json
import shutil
from pathlib import Path

import yaml
from bx_py_utils.path import assert_is_dir, assert_is_file

from manageprojects.cookiecutter_templates import run_cookiecutter, update_project
from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.git import Git
from manageprojects.tests.base import BaseTestCase
from manageprojects.tests.utilities.fixtures import copy_fixtures
from manageprojects.tests.utilities.git_utils import init_git
from manageprojects.tests.utilities.temp_utils import TemporaryDirectory
from manageprojects.utilities.pyproject_toml import parse_pyproject_toml


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

            # pyproject.toml created?
            pyproject_toml_path = result.pyproject_toml_path
            assert_is_file(pyproject_toml_path)
            self.assertEqual(pyproject_toml_path.name, 'pyproject.toml')
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'manageprojects': {
                        'initial_revision': '84d23bf',
                        'initial_date': '2022-10-24T19:15:47+02:00',
                    }
                },
            )

    def test_start_project(self):
        with TemporaryDirectory(prefix='test_start_project_') as main_temp_path:

            directory_rev1 = 'template-rev1'
            template_rev1_path = main_temp_path / directory_rev1
            template_file_rev1_path = (
                template_rev1_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )

            directory_rev2 = 'template-rev2'
            template_rev2_path = main_temp_path / directory_rev2
            template_file_rev2_path = (
                template_rev2_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )
            new_file_rev2_path = template_rev2_path / '{{cookiecutter.dir_name}}' / 'new_file.py'

            cookiecutter_destination = main_temp_path / 'cookiecutter_output_dir'
            project_path = cookiecutter_destination / 'default_directory_name'

            #########################################################################
            # copy existing cookiecutter template to /tmp/:

            copy_fixtures(
                fixtures_dir_name='cookiecutter_simple_template_rev1',
                destination=template_rev1_path,
            )
            assert_is_file(template_file_rev1_path)

            #########################################################################
            # Make git repro and commit the current state:

            git, git_hash1 = init_git(template_rev1_path)
            self.assertEqual(len(git_hash1), 7)

            file_paths = git.ls_files(verbose=False)
            expected_paths = [
                Path(template_rev1_path / 'cookiecutter.json'),
                template_file_rev1_path,
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

            replay_file_path = replay_dir_path / f'{directory_rev1}.json'

            self.assertFalse(cookiecutter_destination.exists())
            self.assertFalse(cookiecutters_dir.exists())
            self.assertFalse(replay_file_path.exists())
            self.assertFalse(project_path.exists())

            from manageprojects.cli import start_project  # import loops

            result: CookiecutterResult = start_project(
                template=str(template_rev1_path),
                destination=cookiecutter_destination,
                no_input=True,
                directory=directory_rev1,
                config_file=config_file_path,
            )

            assert_is_dir(project_path)
            self.assertFalse(cookiecutters_dir.exists())  # no git clone, because local repo?
            assert_is_file(replay_file_path)

            self.assertIsInstance(result, CookiecutterResult)
            self.assertEqual(result.git_path, template_rev1_path)

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
                        '_template': str(template_rev1_path),
                        '_output_dir': str(cookiecutter_destination),
                    }
                },
            )

            # Check created file:
            destination_file_path = project_path / 'default_file_name.py'
            assert_is_file(destination_file_path)
            filecmp.cmp(destination_file_path, template_file_rev1_path)

            # Check created toml file:
            pyproject_toml_path = project_path / 'pyproject.toml'
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertIsInstance(meta, ManageProjectsMeta)
            self.assertEqual(meta.initial_revision, git_hash1)
            self.assertEqual(meta.applied_migrations, [])
            self.assert_datetime_now_range(meta.initial_date, max_diff_sec=5)

            #########################################################################
            # Change the source template and update the existing project

            shutil.copytree(template_rev1_path, template_rev2_path)
            assert_is_file(template_file_rev2_path)
            git = Git(cwd=template_rev2_path)

            # Add a new template file:
            new_file_rev2_path.write_text('print("This is a new added file in template rev2')
            git.add('.', verbose=False)
            git.commit('Add a new file', verbose=False)
            git_hash2 = git.get_current_hash(verbose=False)

            # Change a existing file:
            with template_file_rev2_path.open('a') as f:
                f.write('\n# This comment was added in rev2 ;)\n')
            git.add('.', verbose=False)
            git.commit('Update existing file', verbose=False)
            git_hash3 = git.get_current_hash(verbose=False)

            log_lines = git.log(format='%h - %s', verbose=False)
            self.assertEqual(
                log_lines,
                [
                    f'{git_hash3} - Update existing file',
                    f'{git_hash2} - Add a new file',
                    f'{git_hash1} - The initial commit ;)',
                ],
            )

            # TODO: Test updating the project ;)
            with self.assertRaises(NotImplementedError):
                update_project(project_path=project_path)
