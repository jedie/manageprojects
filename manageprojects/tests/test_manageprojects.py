import json
from pathlib import Path
from unittest import TestCase

import tomli
import yaml
from bx_py_utils.path import assert_is_dir, assert_is_file
from bx_py_utils.test_utils.datetime import parse_dt
from bx_py_utils.test_utils.snapshot import assert_text_snapshot

from manageprojects.cli import start_project
from manageprojects.cookiecutter_templates import (
    CookiecutterResult,
    ManageProjectsMeta,
    get_last_git_hash,
    parse_pyproject_toml,
    run_cookiecutter,
    update_pyproject_toml,
)
from manageprojects.tests.utilities.temp_utils import TemporaryDirectory


class ManageProjectsTestCase(TestCase):
    def assert_tomli(self, path: Path, expected_toml):
        assert_is_file(path)
        toml_dict = tomli.loads(path.read_text(encoding='UTF-8'))
        self.assertDictEqual(toml_dict, expected_toml)

    def test_pyproject_toml_utils(self):
        with TemporaryDirectory(prefix='test_update_pyproject_toml_') as temp_path:
            pyproject_toml_path = temp_path / 'pyproject.toml'
            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0001',
                    commit_date=parse_dt('2000-01-01T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                    }
                },
            )
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertIsInstance(meta, ManageProjectsMeta)
            self.assertEqual(
                meta,
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+00:00'),
                    applied_migrations=[],
                ),
            )
            last_migration_hash = get_last_git_hash(pyproject_toml_path)
            self.assertEqual(last_migration_hash, 'abc0001')

            # Insert "prefix" user data into 'pyproject.toml':
            origin = pyproject_toml_path.read_text()
            new = f'[project]\nname = "foo bar"\n\n\n{origin}'
            pyproject_toml_path.write_text(new)

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0002',
                    commit_date=parse_dt('2000-02-02T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002'],
                    },
                },
            )
            last_migration_hash = get_last_git_hash(pyproject_toml_path)
            self.assertEqual(last_migration_hash, 'abc0002')

            # Append "suffix" user data into 'pyproject.toml':
            origin = pyproject_toml_path.read_text()
            new = f'{origin}\n\n[foo]\nbar = 1\n'
            pyproject_toml_path.write_text(new)

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0003',
                    commit_date=None,  # No: commit_date
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002', 'abc0003'],
                    },
                    'foo': {'bar': 1},  # suffix user data
                },
            )
            last_migration_hash = get_last_git_hash(pyproject_toml_path)
            self.assertEqual(last_migration_hash, 'abc0003')

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0004',
                    commit_date=parse_dt('2000-04-04T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002', 'abc0003', 'abc0004'],
                    },
                    'foo': {'bar': 1},  # suffix user data
                },
            )
            self.assertEqual(
                parse_pyproject_toml(pyproject_toml_path),
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+00:00'),
                    applied_migrations=['abc0002', 'abc0003', 'abc0004'],
                ),
            )
            last_migration_hash = get_last_git_hash(pyproject_toml_path)
            self.assertEqual(last_migration_hash, 'abc0004')

            assert_text_snapshot(got=pyproject_toml_path.read_text())

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
            cookiecutter_destination = main_temp_path / 'cookiecutter_output_dir'
            assert replay_file_path.exists() is False
            assert cookiecutter_destination.exists() is False
            assert cookiecutters_dir.exists() is False

            result: CookiecutterResult = start_project(
                template=cookiecutter_template,
                destination=cookiecutter_destination,
                no_input=True,
                directory=directory,
                config_file=config_file_path,
            )
            self.assertIsInstance(result, CookiecutterResult)
            git_path = cookiecutters_dir / repro_name
            self.assertEqual(result.git_path, git_path)
            assert_is_dir(git_path)  # Checkout was made?
            assert_is_dir(cookiecutter_destination)  # Created from cookiecutter ?

            # Cookiecutter creates a replay JSON?
            assert_is_file(replay_file_path)
            replay_json = replay_file_path.read_text()
            replay_data = json.loads(replay_json)
            assert replay_data == {
                'cookiecutter': {
                    'dir_name': 'directory_name',  # <<< Template defaults!
                    'file_name': 'file_name1',  # <<< Template defaults!
                    '_template': cookiecutter_template,
                    '_output_dir': str(cookiecutter_destination),
                }
            }

            # Our replay config was used?
            assert_is_file(cookiecutter_destination / 'directory_name' / 'file_name1.py')
