import subprocess
from importlib.metadata import version
from pathlib import Path

import manageprojects

BASE_PATH = Path(manageprojects.__file__).parent.parent


def test_version():
    current_version = manageprojects.__version__
    assert version('manageprojects') == current_version

    mp_bin = BASE_PATH / 'mp.py'
    assert mp_bin.is_file()

    output = subprocess.check_output([mp_bin, 'version'], text=True)
    assert f'manageprojects v{current_version}' in output
