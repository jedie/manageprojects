import tempfile
from pathlib import Path, PosixPath
from unittest import mock
from unittest.mock import MagicMock, patch

from bx_py_utils.test_utils.redirect import RedirectOut
from cli_base.cli_tools.test_utils.rich_test_utils import NoColorEnvRich

from manageprojects import cli_app, cli_dev
from manageprojects.cli_app import manage
from manageprojects.constants import PY_BIN_PATH
from manageprojects.data_classes import CookiecutterResult
from manageprojects.test_utils.subprocess import SimpleRunReturnCallback, SubprocessCallMock
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
        with (
            NoColorEnvRich(),
            mock.patch.object(manage, 'start_managed_project', MagicMock(return_value=result)) as m,
            RedirectOut() as buffer,
        ):
            cli_app.main(
                args=(
                    'start-project',
                    'https://github.com/jedie/cookiecutter_templates/',
                    '--directory',
                    'uv-python',
                    'foobar/',
                )
            )
        m.assert_called_once_with(
            template='https://github.com/jedie/cookiecutter_templates/',
            checkout=None,
            output_dir=PosixPath('foobar'),
            input=False,
            replay=False,
            password=None,
            directory='uv-python',
            config_file=None,
        )
        self.assertEqual(buffer.stderr, '')
        self.assert_in_content(
            got=buffer.stdout,
            parts=(
                'https://github.com/jedie/cookiecutter_templates/',
                'foobar',
                'git hash 1234',
            ),
        )

    def test_update_project_cli(self):
        tempdir = tempfile.gettempdir()

        with (
            NoColorEnvRich(),
            mock.patch.object(manage, 'update_managed_project') as m,
            RedirectOut() as buffer,
        ):
            cli_app.main(args=('update-project', tempdir))

        m.assert_called_once_with(
            project_path=Path(tempdir),
            overwrite=True,
            password=None,
            config_file=None,
            cleanup=True,
            input=False,
        )
        self.assertEqual(buffer.stderr, '')
        self.assert_in_content(
            got=buffer.stdout,
            parts=(
                f'Update project: "{tempdir}"...',
                f'Managed project "{tempdir}" updated, ok.',
            ),
        )

    def test_install(self):
        with (
            NoColorEnvRich(),
            patch('manageprojects.cli_dev.print_version'),
            SubprocessCallMock(return_callback=SimpleRunReturnCallback(stdout='')) as call_mock,
            RedirectOut() as buffer,
        ):
            cli_dev.main(args=('install',))

        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(PY_BIN_PATH,)),
            [
                ['.../uv', 'sync'],
                ['.../pip', 'install', '--no-deps', '-e', '.'],
            ],
        )
        self.assertEqual(buffer.stderr, '')
        self.assert_in_content(
            got=buffer.stdout,
            parts=(
                '/manageprojects$ .venv/bin/uv sync',
                '/manageprojects$ .venv/bin/pip install --no-deps -e .',
            ),
        )
