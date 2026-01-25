import datetime
import shutil
from pathlib import Path
from pprint import pprint
from unittest import TestCase

from bx_py_utils.path import assert_is_file

from manageprojects.utilities.pyproject_toml import TomlDocument, get_toml_document


GIT_BIN_PARENT = Path(shutil.which('git')).parent


class BaseTestCase(TestCase):
    maxDiff = None

    def assert_toml(self, path: Path, expected: dict):
        toml_document: TomlDocument = get_toml_document(path)
        got = toml_document.doc.unwrap()  # TOMLDocument -> dict
        try:
            self.assertDictEqual(got, expected)
        except AssertionError:
            print('-' * 79)
            pprint(got)
            print('-' * 79)
            raise

    def assert_datetime_range(
        self, dt: datetime.datetime, reference: datetime.datetime, max_diff_sec: int = 5
    ):
        self.assertEqual(dt.tzinfo, reference.tzinfo)
        diff = datetime.timedelta(seconds=max_diff_sec)
        min_dt = reference - diff
        max_dt = reference + diff
        self.assertLessEqual(dt, max_dt)
        self.assertGreaterEqual(dt, min_dt)

    def assert_datetime_now_range(self, dt: datetime.datetime, max_diff_sec: int = 5):
        now = datetime.datetime.now(tz=dt.tzinfo)
        self.assert_datetime_range(dt=dt, reference=now, max_diff_sec=max_diff_sec)

    def assert_content(self, got: str, expected: str, strip=True):
        if strip:
            got = got.strip()
            expected = expected.strip()

        try:
            self.assertEqual(got, expected)
        except AssertionError as err:
            error_message = (
                '∨∨∨∨∨∨∨∨∨∨∨∨ [Content start] ∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨∨\n'
                f'{got}\n'
                '∧∧∧∧∧∧∧∧∧∧∧∧ [Content end] ∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧∧\n'
                f'{err}\n'
                '================================================================================================\n\n'
            )
            raise AssertionError(error_message)

    def assert_file_content(self, path: Path, content: str):
        assert_is_file(path)
        file_content = path.read_text().strip()
        self.assert_content(got=file_content, expected=content)
