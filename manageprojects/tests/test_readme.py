from bx_py_utils.auto_doc import assert_readme_block
from bx_py_utils.path import assert_is_file

from manageprojects import constants
from manageprojects.cli.cli_app import cli
from manageprojects.cli.dev import PACKAGE_ROOT
from manageprojects.cli.dev import cli as dev_cli
from manageprojects.test_utils.click_cli_utils import invoke_click
from manageprojects.tests.base import BaseTestCase


def assert_cli_help_in_readme(text_block: str, marker: str):
    README_PATH = PACKAGE_ROOT / 'README.md'
    assert_is_file(README_PATH)

    text_block = text_block.replace(constants.CLI_EPILOG, '')
    text_block = f'```\n{text_block.strip()}\n```'
    assert_readme_block(
        readme_path=README_PATH,
        text_block=text_block,
        start_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} start ✂✂✂)',
        end_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} end ✂✂✂)',
    )


class ReadmeTestCase(BaseTestCase):
    def test_main_help(self):
        stdout = invoke_click(cli, '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...',
                ' start-project ',
                ' update-project ',
                constants.CLI_EPILOG,
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='main help')

    def test_dev_help(self):
        stdout = invoke_click(dev_cli, '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./dev-cli.py [OPTIONS] COMMAND [ARGS]...',
                ' check-code-style ',
                ' coverage ',
                constants.CLI_EPILOG,
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='dev help')

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
        assert_cli_help_in_readme(text_block=stdout, marker='start-project help')

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
        assert_cli_help_in_readme(text_block=stdout, marker='update-project help')

    def test_format_file_help(self):
        stdout = invoke_click(cli, 'format-file', '--help')
        self.assert_in_content(
            got=stdout,
            parts=(
                'Usage: ./cli.py format-file [OPTIONS] FILE_PATH',
                '--py-version',
                '--max-line-length',
                '--darker-prefixes',
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='format-file help')
