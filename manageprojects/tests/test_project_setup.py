import subprocess
from pathlib import Path

import tomli

import manageprojects
from manageprojects.path_utils import assert_is_dir, assert_is_file

PACKAGE_ROOT = Path(manageprojects.__file__).parent.parent
assert_is_dir(PACKAGE_ROOT)
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')


def test_version():
    pyproject_toml_path = Path(PACKAGE_ROOT, 'pyproject.toml')
    pyproject_toml = tomli.loads(pyproject_toml_path.read_text(encoding='UTF-8'))
    pyproject_version = pyproject_toml['project']['version']

    current_version = manageprojects.__version__
    assert current_version == pyproject_version

    mp_bin = PACKAGE_ROOT / 'mp.py'
    assert_is_file(mp_bin)

    output = subprocess.check_output([mp_bin, 'version'], text=True)
    assert f'manageprojects v{current_version}' in output
