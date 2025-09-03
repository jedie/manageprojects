import filecmp
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import TestCase

from bx_py_utils.path import assert_is_file

from manageprojects.setup_python import main
from manageprojects.utilities.include_setup_python import SOURCE_PATH, IncludeSetupPythonBaseTestCase


class SetupPythonTestCase(TestCase):
    def test_use_system_python(self):
        major_version = f'{sys.version_info.major}.{sys.version_info.minor}'

        python_path = main(args=(major_version,))
        self.assertIsInstance(python_path, Path)
        assert_is_file(python_path)

        process = subprocess.run([str(python_path), '-V'], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0)
        output = process.stdout.strip()
        assert output.startswith(f'Python {major_version}.'), f'{output=}'


class IncludeSetupPythonTestCase(IncludeSetupPythonBaseTestCase):
    maxDiff = None

    def test_auto_update_setup_python(self):
        self.assertIsNone(self.DESTINATION_PATH)
        self.assertEqual(SOURCE_PATH.name, 'setup_python.py')

        with tempfile.TemporaryDirectory() as temp_dir:
            self.DESTINATION_PATH = Path(temp_dir) / 'test.py'

            with self.assertRaises(AssertionError) as cm:
                self.auto_update_setup_python()

            self.assertIn('File does not exists', str(cm.exception))

            self.DESTINATION_PATH.write_text('OLD')
            self.assertFalse(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))

            with self.assertRaises(AssertionError) as cm:
                self.auto_update_setup_python()
            self.assertIn(' updated, please commit ', str(cm.exception))

            self.assertTrue(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))

            result = self.auto_update_setup_python()
            self.assertIsNone(result)
            self.assertTrue(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))
