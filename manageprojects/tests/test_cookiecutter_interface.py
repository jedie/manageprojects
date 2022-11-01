from bx_py_utils.path import assert_is_dir, assert_is_file

from manageprojects.cookiecutter_interface import cookiecutter_generate_files
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.temp_path import TemporaryDirectory


class CookiecutterInterfaceTestCase(BaseTestCase):
    def test_cookiecutter_generate_files(self):
        with TemporaryDirectory(prefix='test_cookiecutter_generate_files_') as main_temp_path:
            repo_dir_path = main_temp_path / 'repo_dir'
            output_dir_path = main_temp_path / 'output_dir'
            project_dir_path = output_dir_path / 'test-dir'
            destination_file_path = project_dir_path / 'test-file.py'

            source_file_path = (
                repo_dir_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'
            )
            source_file_path.parent.mkdir(parents=True)
            source_file_path.write_text('print("Hello World: {{ cookiecutter.value }}")')

            project_dir = cookiecutter_generate_files(
                repo_dir=repo_dir_path,
                replay_context={
                    'cookiecutter': {
                        'dir_name': 'test-dir',
                        'file_name': 'test-file',
                        'value': 'test-value',
                    }
                },
                output_dir=output_dir_path,
            )
            self.assertEqual(project_dir, str(project_dir_path))
            assert_is_dir(project_dir_path)
            assert_is_file(destination_file_path)
            self.assert_file_content(destination_file_path, 'print("Hello World: test-value")')

            # Change the context and source file and overwrite new results:
            source_file_path.write_text('print("Hello WORLD: {{ cookiecutter.value }} !")')
            project_dir = cookiecutter_generate_files(
                repo_dir=repo_dir_path,
                replay_context={
                    'cookiecutter': {
                        'dir_name': 'test-dir',
                        'file_name': 'test-file',
                        'value': 'OTHER VALUE',
                    }
                },
                output_dir=output_dir_path,
            )
            self.assertEqual(project_dir, str(project_dir_path))
            self.assert_file_content(destination_file_path, 'print("Hello WORLD: OTHER VALUE !")')
