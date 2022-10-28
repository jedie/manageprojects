import shutil
from pathlib import Path

from bx_py_utils.path import assert_is_dir

from mp import BASE_PATH


FIXTUES_PATH = BASE_PATH / 'manageprojects' / 'tests' / 'fixtures'
assert_is_dir(FIXTUES_PATH)


def copy_fixtures(*, fixtures_dir_name: str, destination: Path) -> None:
    fixtues_path = FIXTUES_PATH / fixtures_dir_name
    assert_is_dir(fixtues_path)
    shutil.copytree(fixtues_path, destination)
    assert_is_dir(destination)
