import subprocess
from pathlib import Path
from unittest import TestCase

import tomli
from bx_py_utils.path import assert_is_file

import manageprojects
from manageprojects import __version__
from manageprojects.cli.cli_app import check_code_style, fix_code_style


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent


class ProjectSetupTestCase(TestCase):
    def test_version(self):
        pyproject_toml_path = Path(PACKAGE_ROOT, 'pyproject.toml')
        assert_is_file(pyproject_toml_path)

        self.assertIsNotNone(__version__)

        pyproject_toml = tomli.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
        pyproject_version = pyproject_toml['project']['version']

        self.assertEqual(__version__, pyproject_version)

        cli_bin = PACKAGE_ROOT / 'cli.py'
        assert_is_file(cli_bin)

        output = subprocess.check_output([cli_bin, 'version'], text=True)
        self.assertIn(f'manageprojects v{__version__}', output)

    def test_code_style(self):
        try:
            fix_code_style()
        except SystemExit as err:
            self.assertEqual(err.code, 0)
        else:
            raise AssertionError('No sys.exit() !')

        try:
            check_code_style(verbose=False)
        except SystemExit as err:
            self.assertEqual(err.code, 0)
        else:
            raise AssertionError('No sys.exit() !')
