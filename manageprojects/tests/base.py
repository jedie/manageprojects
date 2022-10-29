import datetime
from pathlib import Path
from unittest import TestCase

import tomli
from bx_py_utils.path import assert_is_file


class BaseTestCase(TestCase):
    maxDiff = None

    def assert_tomli(self, path: Path, expected_toml):
        assert_is_file(path)
        toml_dict = tomli.loads(path.read_text(encoding='UTF-8'))
        self.assertDictEqual(toml_dict, expected_toml)

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

    def assert_file_content(self, path: Path, content: str):
        assert_is_file(path)
        file_content = path.read_text().strip()
        content = content.strip()
        try:
            self.assertEqual(file_content, content)
        except AssertionError:
            print('-' * 79)
            print(file_content)
            print('-' * 79)
            raise
