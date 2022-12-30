import inspect
from pathlib import Path

from bx_py_utils.path import assert_is_dir

from manageprojects.cookiecutter_api import get_repo_path
from manageprojects.test_utils.logs import AssertLogs
from manageprojects.tests.base import BaseTestCase


class CookiecutterApiTestCase(BaseTestCase):
    def test_get_repo_path(self):
        repro_name = 'mp_test_template1'
        cookiecutter_template = f'https://github.com/jedie/{repro_name}/'
        directory = 'test_template1'

        with AssertLogs(self) as logs:
            repo_path = get_repo_path(
                template=cookiecutter_template,
                directory=directory,
                checkout='84d23bf',  # Old version
            )
        logs.assert_in('repo_dir', repo_path)

        self.assertIsInstance(repo_path, Path)
        self.assertEqual(repo_path.name, directory)
        assert_is_dir(repo_path.parent / '.git')

        test_file_path = Path(
            repo_path, '{{cookiecutter.dir_name}}', '{{cookiecutter.file_name}}.py'
        )
        self.assert_file_content(
            test_file_path,
            inspect.cleandoc(
                '''
                print('Hello World 1')
                '''
            ),
        )

        with AssertLogs(self) as logs:
            repo_path = get_repo_path(
                template=cookiecutter_template,
                directory=directory,
                checkout=None,  # Current main branch
            )
        logs.assert_in('repo_dir', repo_path)

        self.assertIsInstance(repo_path, Path)
        self.assertEqual(repo_path.name, directory)
        assert_is_dir(repo_path.parent / '.git')

        test_file_path = Path(
            repo_path, '{{cookiecutter.dir_name}}', '{{cookiecutter.file_name}}.py'
        )
        self.assert_file_content(
            test_file_path,
            inspect.cleandoc(
                '''
                # A later added Comment...

                print('Hello World 1')
                '''
            ),
        )
