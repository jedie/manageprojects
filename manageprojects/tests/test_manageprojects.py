import json
from unittest import TestCase

import yaml

from manageprojects.cli import start_project
from manageprojects.cookiecutter_templates import run_cookiecutter
from manageprojects.path_utils import assert_is_dir, assert_is_file
from manageprojects.tests.utilities.temp_utils import TemporaryDirectory


class ManageProjectsTestCase(TestCase):
    def test_run_cookiecutter(self):
        cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
        directory = "test_template1"

        with TemporaryDirectory(prefix="manageprojects_") as main_temp_path:
            replay_dir_path = main_temp_path / ".cookiecutter_replay"
            replay_dir_path.mkdir()

            cookiecutters_dir = main_temp_path / ".cookiecutters"
            config = {
                "cookiecutters_dir": str(cookiecutters_dir),
                "replay_dir": str(replay_dir_path),
            }
            config_yaml = yaml.dump(config)
            config_file_path = main_temp_path / "cookiecutter_config.yaml"
            config_file_path.write_text(config_yaml)

            replay_file_path = replay_dir_path / f"{directory}.json"
            cookiecutter_output_dir = main_temp_path / "cookiecutter_output_dir"
            assert replay_file_path.exists() is False
            assert cookiecutter_output_dir.exists() is False
            assert cookiecutters_dir.exists() is False

            run_cookiecutter(
                template=cookiecutter_template,
                output_dir=cookiecutter_output_dir,
                no_input=True,
                directory=directory,
                config_file=config_file_path,
                extra_context={
                    "dir_name": "a_dir_name",
                    "file_name": "a_file_name",
                },
            )
            assert_is_dir(cookiecutters_dir)  # Checkout was made?
            assert_is_dir(cookiecutter_output_dir)  # Created from cookiecutter ?

            # Cookiecutter creates a replay JSON?
            assert_is_file(replay_file_path)
            replay_json = replay_file_path.read_text()
            replay_data = json.loads(replay_json)
            assert replay_data == {
                "cookiecutter": {
                    "dir_name": "a_dir_name",
                    "file_name": "a_file_name",
                    "_template": cookiecutter_template,
                    "_output_dir": str(cookiecutter_output_dir),
                }
            }

            # Our replay config was used?
            assert_is_file(cookiecutter_output_dir / "a_dir_name" / "a_file_name.py")

    def test_start_project(self):
        cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
        directory = "test_template1"

        with TemporaryDirectory(prefix="manageprojects_") as main_temp_path:
            replay_dir_path = main_temp_path / ".cookiecutter_replay"
            replay_dir_path.mkdir()

            cookiecutters_dir = main_temp_path / ".cookiecutters"
            config = {
                "cookiecutters_dir": str(cookiecutters_dir),
                "replay_dir": str(replay_dir_path),
            }
            config_yaml = yaml.dump(config)
            config_file_path = main_temp_path / "cookiecutter_config.yaml"
            config_file_path.write_text(config_yaml)

            replay_file_path = replay_dir_path / f"{directory}.json"
            cookiecutter_destination = main_temp_path / "cookiecutter_output_dir"
            assert replay_file_path.exists() is False
            assert cookiecutter_destination.exists() is False
            assert cookiecutters_dir.exists() is False

            start_project(
                template=cookiecutter_template,
                destination=cookiecutter_destination,
                no_input=True,
                directory=directory,
                config_file=config_file_path,
            )
            assert_is_dir(cookiecutters_dir)  # Checkout was made?
            assert_is_dir(cookiecutter_destination)  # Created from cookiecutter ?

            # Cookiecutter creates a replay JSON?
            assert_is_file(replay_file_path)
            replay_json = replay_file_path.read_text()
            replay_data = json.loads(replay_json)
            assert replay_data == {
                "cookiecutter": {
                    "dir_name": "directory_name",  # <<< Template defaults!
                    "file_name": "file_name1",  # <<< Template defaults!
                    "_template": cookiecutter_template,
                    "_output_dir": str(cookiecutter_destination),
                }
            }

            # Our replay config was used?
            assert_is_file(cookiecutter_destination / "directory_name" / "file_name1.py")
