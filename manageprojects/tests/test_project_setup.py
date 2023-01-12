import subprocess
from pathlib import Path

import tomli
from bx_py_utils.path import assert_is_file
from bx_py_utils.test_utils.redirect import RedirectOut

import manageprojects
from manageprojects import __version__
from manageprojects.cli.cli_app import check_code_style, fix_code_style
from manageprojects.tests.base import BaseTestCase


PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent


class ProjectSetupTestCase(BaseTestCase):
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
        with RedirectOut() as buffer:
            try:
                check_code_style(verbose=False)
            except SystemExit as err:
                if err.code == 0:
                    self.assertEqual(buffer.stderr, '')
                    self.assert_in_content(
                        got=buffer.stdout,
                        parts=(
                            '.venv/bin/darker',
                            '.venv/bin/flake8',
                            'Code style: OK',
                        ),
                    )
                    return  # Code style is ok -> Nothing to fix ;)
            else:
                raise AssertionError('No sys.exit() !')

        # Try to "auto" fix code style:

        with RedirectOut() as buffer:
            try:
                fix_code_style(verbose=False)
            except SystemExit as err:
                self.assertEqual(err.code, 0, 'Code style can not be fixed, see output above!')
            else:
                raise AssertionError('No sys.exit() !')

        self.assertEqual(buffer.stderr, '')
        self.assert_in_content(
            got=buffer.stdout,
            parts=(
                '.venv/bin/darker',
                'Code style fixed, OK.',
            ),
        )
