from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_file

from manageprojects.test_utils.temp_utils import TempContentFile


class TempUtilsTestCase(TestCase):
    def test_temp_content_file(self):
        with TempContentFile("Foo Bar") as file_path:
            assert isinstance(file_path, Path)
            assert_is_file(file_path)
            assert Path(file_path).read_text() == "Foo Bar"
        assert file_path.exists() is False

        with TempContentFile("", prefix="pre", suffix=".suf") as file_path:
            file_name = file_path.name
            assert file_name.startswith("pre")
            assert file_name.endswith(".suf")
            assert file_path.suffixes == [".suf"]
