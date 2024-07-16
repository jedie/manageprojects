from unittest.mock import patch

from click.testing import Result

from manageprojects.cli_app import cli, manage
from manageprojects.test_utils.click_cli_utils import ClickInvokeCliException, invoke_click
from manageprojects.tests.base import BaseTestCase


class CliTestCase(BaseTestCase):
    def test_invoke_click(self):
        with patch.object(manage, 'format_one_file', side_effect=RuntimeError('Bam!')):
            with self.assertRaises(ClickInvokeCliException) as cm:
                invoke_click(cli, 'format-file', __file__)

        self.assertIsInstance(cm.exception, ClickInvokeCliException)
        self.assertIsInstance(cm.exception.result, Result)
        self.assertEqual(cm.exception.result.stdout, '')
        self.assertEqual(cm.exception.result.stderr, '')
        self.assertIsInstance(cm.exception.result.exception, RuntimeError)
        self.assertEqual(cm.exception.result.exception.args, ('Bam!',))
