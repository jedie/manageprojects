import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from manageprojects.cli import cli_app
from manageprojects.cli.cli_app import start_project, update_project
from manageprojects.cli.dev import PACKAGE_ROOT
from manageprojects.cli.dev import cli as dev_cli
from manageprojects.constants import PY_BIN_PATH
from manageprojects.data_classes import CookiecutterResult
from manageprojects.test_utils.click_cli_utils import invoke_click
from manageprojects.test_utils.subprocess import SubprocessCallMock
from manageprojects.tests.base import BaseTestCase


class CliTestCase(BaseTestCase):

    def test_start_project_cli(self):
        result = CookiecutterResult(
            destination_path=Path('destination'),
            git_path=Path('git-path'),
            git_hash='1234',
            commit_date=None,
            cookiecutter_context=dict(foo=1, bar=2),
        )
        with mock.patch.object(cli_app, 'start_managed_project', MagicMock(return_value=result)) as m:
            stdout = invoke_click(
                start_project,
                'https://github.com/jedie/cookiecutter_templates/',
                '--directory',
                'piptools-python',
                'foobar/',
            )
        m.assert_called_once_with(
            template='https://github.com/jedie/cookiecutter_templates/',
            directory='piptools-python',
            output_dir=Path('foobar'),
            checkout=None,
            input=True,
            replay=False,
            password=None,
            config_file=None,
        )
        self.assert_in_content(
            got=stdout,
            parts=(
                'https://github.com/jedie/cookiecutter_templates/',
                'foobar',
                'git hash 1234',
            ),
        )

    def test_update_project_cli(self):
        tempdir = tempfile.gettempdir()

        with mock.patch.object(cli_app, 'update_managed_project') as m:
            stdout = invoke_click(update_project, tempdir)

        m.assert_called_once_with(
            project_path=Path(tempdir),
            overwrite=True,
            password=None,
            config_file=None,
            cleanup=True,
            input=False,
        )
        self.assert_in_content(
            got=stdout,
            parts=(
                f'Update project: "{tempdir}"...',
                f'Managed project "{tempdir}" updated, ok.',
            ),
        )

    def test_install(self):
        with SubprocessCallMock() as call_mock:
            invoke_click(dev_cli, 'install')

        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(PY_BIN_PATH,)),
            [
                ['.../pip-sync', f'{PACKAGE_ROOT}/requirements.dev.txt'],
                ['.../pip', 'install', '--no-deps', '-e', '.'],
            ],
        )
