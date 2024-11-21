from bx_py_utils.auto_doc import assert_readme_block
from bx_py_utils.path import assert_is_file
from cli_base.cli_tools.test_utils.rich_test_utils import NoColorEnvRich, invoke

from manageprojects import constants
from manageprojects.cli_dev import PACKAGE_ROOT
from manageprojects.tests.base import BaseTestCase


def remove_until_usage(text: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith('usage: '):
            return '\n'.join(lines[idx:])
    raise ValueError('No usage line found')


def assert_cli_help_in_readme(text_block: str, marker: str):
    README_PATH = PACKAGE_ROOT / 'README.md'
    assert_is_file(README_PATH)

    text_block = text_block.replace(constants.CLI_EPILOG, '')
    text_block = remove_until_usage(text_block)
    text_block = f'```\n{text_block.strip()}\n```'

    assert_readme_block(
        readme_path=README_PATH,
        text_block=text_block,
        start_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} start ✂✂✂)',
        end_marker_line=f'[comment]: <> (✂✂✂ auto generated {marker} end ✂✂✂)',
    )


class ReadmeTestCase(BaseTestCase):
    def test_main_help(self):
        with NoColorEnvRich():
            stdout = invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=['--help'], strip_line_prefix='usage: ')
        self.assert_in_content(
            got=stdout,
            parts=(
                'usage: ./cli.py [-h]',
                ' version ',
                'Print version and exit',
                constants.CLI_EPILOG,
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='main help')

    def test_dev_help(self):
        with NoColorEnvRich():
            stdout = invoke(cli_bin=PACKAGE_ROOT / 'dev-cli.py', args=['--help'], strip_line_prefix='usage: ')
        self.assert_in_content(
            got=stdout,
            parts=(
                'usage: ./dev-cli.py [-h]',
                ' lint ',
                ' coverage ',
                ' update-readme-history ',
                ' publish ',
                constants.CLI_EPILOG,
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='dev help')

    def test_start_project_help(self):
        with NoColorEnvRich():
            stdout = invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=('start-project', '--help'))
        self.assert_in_content(
            got=stdout,
            parts=(
                'usage: ./cli.py start-project [-h] ',
                ' --directory ',
                ' --input, --no-input ',
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='start-project help')

    def test_update_project_help(self):
        with NoColorEnvRich():
            stdout = invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=('update-project', '--help'))
        self.assert_in_content(
            got=stdout,
            parts=(
                'usage: ./cli.py update-project [-h] ',
                ' --input, --no-input ',
                ' --cleanup, --no-cleanup ',
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='update-project help')

    def test_format_file_help(self):
        with NoColorEnvRich():
            stdout = invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=('format-file', '--help'))
        self.assert_in_content(
            got=stdout,
            parts=(
                'usage: ./cli.py format-file [-h] ',
                ' --py-version ',
                ' --max-line-length ',
            ),
        )
        assert_cli_help_in_readme(text_block=stdout, marker='format-file help')
