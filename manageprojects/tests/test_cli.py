from pathlib import Path
from unittest.mock import patch

from bx_py_utils.path import assert_is_dir, assert_is_file
from bx_py_utils.test_utils.snapshot import assert_text_snapshot
from typer import rich_utils
from typer.testing import CliRunner

import manageprojects
from manageprojects import __version__
from manageprojects.cli.cli_app import app
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.subprocess_utils import verbose_check_output


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent
assert_is_dir(PACKAGE_ROOT)
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')


class CliTestCase(BaseTestCase):
    def invoke(self, *args, expected_strerr=''):
        with patch.object(rich_utils, 'MAX_WIDTH', 100), patch.object(
            rich_utils, 'FORCE_TERMINAL', False
        ):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(app, args, color=False)
            stdout = result.stdout
            stderr = result.stderr
            self.assertEqual(stderr, expected_strerr)
            self.assertEqual(result.exit_code, 0, f'{result}:\n{stdout}')
            return stdout

    def test_main_help(self):
        stdout = self.invoke('--help')
        self.assertIn('Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...', stdout)
        self.assertIn('start-project', stdout)
        self.assertIn('update-project', stdout)
        assert_text_snapshot(got=stdout)

    def test_start_project_help(self):
        stdout = self.invoke('start-project', '--help')
        self.assertIn('Usage: ./cli.py start-project [OPTIONS] [TEMPLATE] [OUTPUT_DIR]', stdout)
        self.assertIn('output_dir', stdout)
        self.assertIn('--no-input', stdout)
        assert_text_snapshot(got=stdout)

    def test_update_project_help(self):
        stdout = self.invoke('update-project', '--help')
        self.assertIn('Usage: ./cli.py update-project [OPTIONS] [PROJECT_PATH]', stdout)
        self.assertIn('--no-input', stdout)
        assert_text_snapshot(got=stdout)


class CliDirectTestCase(BaseTestCase):
    def call(self, *args, exit_on_error=True):
        cli_bin = PACKAGE_ROOT / 'cli.py'
        assert_is_file(cli_bin)
        return verbose_check_output(cli_bin, *args, cwd=PACKAGE_ROOT, exit_on_error=exit_on_error)

    def test_install(self):
        output = self.call('install')
        self.assertIn(f'Successfully installed manageprojects-{__version__}\n', output)
