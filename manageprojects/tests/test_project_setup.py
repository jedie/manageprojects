import shutil
import subprocess
from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_file
from bx_py_utils.test_utils.redirect import RedirectOut
from cli_base.cli_tools.code_style import assert_code_style
from cli_base.cli_tools.subprocess_utils import ToolsExecutor
from cli_base.cli_tools.test_utils.assertion import assert_in
from cli_base.cli_tools.test_utils.rich_test_utils import NoColorEnvRich
from packaging.version import Version

from cli import main as main_cli
from manageprojects import __version__
from manageprojects.cli_dev import PACKAGE_ROOT
from manageprojects.test_utils.import_utils import import_from_path
from manageprojects.test_utils.project_setup import check_editor_config, get_py_max_line_length
from manageprojects.test_utils.subprocess import SimpleRunReturnCallback, SubprocessCallMock


class ProjectSetupTestCase(TestCase):
    def test_version(self):
        self.assertIsNotNone(__version__)

        version = Version(__version__)  # Will raise InvalidVersion() if wrong formatted
        self.assertEqual(str(version), __version__)

        cli_bin = PACKAGE_ROOT / 'cli.py'
        assert_is_file(cli_bin)

        output = subprocess.check_output([cli_bin, 'version'], text=True)
        self.assertIn(f'manageprojects v{__version__}', output)

        dev_cli_bin = PACKAGE_ROOT / 'dev-cli.py'
        assert_is_file(dev_cli_bin)

        output = subprocess.check_output([dev_cli_bin, 'version'], text=True)
        self.assertIn(f'manageprojects v{__version__}', output)

    def test_code_style(self):
        return_code = assert_code_style(package_root=PACKAGE_ROOT)
        self.assertEqual(return_code, 0, 'Code style error, see output above!')

    def test_check_editor_config(self):
        check_editor_config(package_root=PACKAGE_ROOT)

        max_line_length = get_py_max_line_length(package_root=PACKAGE_ROOT)
        self.assertEqual(max_line_length, 119)

    def test_pre_commit_hooks(self):
        executor = ToolsExecutor(cwd=PACKAGE_ROOT)
        for command in ('migrate-config', 'validate-config', 'validate-manifest'):
            executor.verbose_check_call('pre-commit', command, exit_on_error=True)

    def test_main_cli(self):
        with NoColorEnvRich(), RedirectOut() as buffer:
            main_cli(argv=('cli.py', 'version'))
        self.assertEqual(buffer.stderr, '')
        assert_in(
            content=buffer.stdout,
            parts=('bin/uv run --active -m manageprojects version',),
        )
        with SubprocessCallMock(return_callback=SimpleRunReturnCallback(stdout='mocked output')) as call_mock:
            main_cli(argv=('cli.py', 'version'))

        rstrip_path = Path(shutil.which('uv')).parent.parent
        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(rstrip_path,)),
            [
                ['.../bin/uv', 'run', '--active', '-m', 'manageprojects', 'version'],
            ],
        )

    def test_dev_cli(self):
        dev_cli = import_from_path(
            module_name='dev_cli',
            file_path=PACKAGE_ROOT / 'dev-cli.py',
        )
        dev_cli_main = dev_cli.main

        with NoColorEnvRich(), RedirectOut() as buffer:
            dev_cli_main(argv=('dev-cli.py', 'version'))
        self.assertEqual(buffer.stderr, '')
        assert_in(
            content=buffer.stdout,
            parts=('bin/uv run --active -m manageprojects.cli_dev version',),
        )
        with SubprocessCallMock(return_callback=SimpleRunReturnCallback(stdout='mocked output')) as call_mock:
            dev_cli_main(argv=('dev-cli.py', 'version'))

        rstrip_path = Path(shutil.which('uv')).parent.parent
        self.assertEqual(
            call_mock.get_popenargs(rstrip_paths=(rstrip_path,)),
            [
                ['.../bin/uv', 'run', '--active', '-m', 'manageprojects.cli_dev', 'version'],
            ],
        )
