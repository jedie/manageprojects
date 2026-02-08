import importlib.util
from pathlib import Path

from bx_py_utils.path import assert_is_file


def import_from_path(*, module_name: str, file_path: Path):
    assert_is_file(file_path)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
