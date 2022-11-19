import subprocess
from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_file

import manageprojects
from manageprojects.cli import PACKAGE_ROOT, check_code_style, fix_code_style, mypy
from manageprojects.utilities.pyproject_toml import toml_load


class ProjectSetupTestCase(TestCase):

    def test_version(self):
        pyproject_toml_path = Path(PACKAGE_ROOT, 'pyproject.toml')
        pyproject_toml = toml_load(pyproject_toml_path)
        pyproject_version = pyproject_toml['project']['version']

        current_version = manageprojects.__version__
        assert (
            current_version == pyproject_version
        ), f'{current_version!r} is not {pyproject_version!r}'

        mp_bin = PACKAGE_ROOT / 'mp.py'
        assert_is_file(mp_bin)

        output = subprocess.check_output([mp_bin, 'version'], text=True)
        assert f'manageprojects v{current_version}' in output

    def test_code_style(self):
        fix_code_style()
        check_code_style(verbose=False)

    def test_mypy(self):
        mypy(verbose=False)
