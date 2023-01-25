import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from bx_py_utils.auto_doc import assert_readme_block
from bx_py_utils.path import assert_is_file
from bx_py_utils.test_utils.snapshot import assert_text_snapshot

import manageprojects
from manageprojects import __version__, constants
from manageprojects.cli import cli_app
from manageprojects.cli.cli_app import cli, start_project, update_project
from manageprojects.data_classes import CookiecutterResult
from manageprojects.test_utils.click_cli_utils import invoke_click, subprocess_cli
from manageprojects.tests.base import BaseTestCase


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')
README_PATH = PACKAGE_ROOT / 'README.md'
assert_is_file(README_PATH)


def assert_cli_help_in_readme(text_block: str, marker: str):
    text_block = text_block.replace(constants.CLI_EPILOG, '')
    text_block = f'```\n{text_block.strip()}\n```'
    assert_readme_block(
        readme_path=README_PATH,
        text_block=text_block,
        start_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} start ✂✂✂)',
        end_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} end ✂✂✂)',
    )


class CliTestCase(BaseTestCase):

    def test_main_help(self):
        stdout = invoke_click(cli, '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...',
                'start-project',
                'update-project',
                constants.CLI_EPILOG,
            ),
        )
        assert_text_snapshot(got=stdout)
        assert_cli_help_in_readme(text_block=stdout, marker='main help')

    def test_start_project_help(self):
        stdout = invoke_click(cli, 'start-project', '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./cli.py start-project [OPTIONS] TEMPLATE OUTPUT_DIR',
                '--directory',
                '--input/--no-input',
            ),
        )
        assert_text_snapshot(got=stdout)
        assert_cli_help_in_readme(text_block=stdout, marker='start-project help')

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

    def test_update_project_help(self):
        stdout = invoke_click(cli, 'update-project', '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./cli.py update-project [OPTIONS] PROJECT_PATH',
                '--input/--no-input',
                '--cleanup/--no-cleanup',
            ),
        )
        assert_text_snapshot(got=stdout)
        assert_cli_help_in_readme(text_block=stdout, marker='update-project help')

    def test_update_project_cli(self):
        tempdir = tempfile.gettempdir()

        with mock.patch.object(cli_app, 'update_managed_project') as m:
            stdout = invoke_click(update_project, tempdir)

        m.assert_called_once_with(
            project_path=Path(tempdir),
            overwrite=False,
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
        output = subprocess_cli(cli_bin=PACKAGE_ROOT / 'cli.py', args=('install',))
        self.assert_in_content(
            got=output,
            parts=(
                'pip install -e .',
                f'Successfully installed manageprojects-{__version__}',
            ),
        )
