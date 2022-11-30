from unittest.mock import patch

from bx_py_utils.test_utils.snapshot import assert_text_snapshot
from typer import rich_utils
from typer.testing import CliRunner

from manageprojects.cli.cli_app import app
from manageprojects.tests.base import BaseTestCase


class CliTestCase(BaseTestCase):
    def invoke(self, *args):
        with patch.object(rich_utils, 'MAX_WIDTH', 100), patch.object(
            rich_utils, 'FORCE_TERMINAL', False
        ):
            runner = CliRunner()
            result = runner.invoke(app, args, color=False)
            self.assertEqual(result.exit_code, 0, result)
            return result.stdout

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
