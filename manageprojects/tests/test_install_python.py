import filecmp
import inspect
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest import TestCase

from bx_py_utils.path import assert_is_file
from rich import print
from rich.rule import Rule

from manageprojects.install_python import extract_versions, get_latest_versions
from manageprojects.tests.docwrite_macros_install_python import EXAMPLE_SCRIPT_PATH
from manageprojects.utilities.include_install_python import SOURCE_PATH, IncludeInstallPythonBaseTestCase


PYTHON_ORG_FTP_HTML = """
<a href="3.11.7/">3.11.7/</a>                                            04-Dec-2023 21:53                   -
<a href="3.11.8/">3.11.8/</a>                                            06-Feb-2024 23:40                   -
<a href="3.11.9/">3.11.9/</a>                                            02-Apr-2024 13:39                   -
<a href="3.12.0/">3.12.0/</a>                                            02-Oct-2023 14:50                   -
<a href="3.12.1/">3.12.1/</a>                                            08-Dec-2023 00:41                   -
<a href="3.12.2/">3.12.2/</a>                                            06-Feb-2024 23:57                   -
<a href="3.12.3/">3.12.3/</a>                                            09-Apr-2024 15:28                   -
<a href="3.12.4/">3.12.4/</a>                                            06-Jun-2024 22:25                   -
<a href="3.12.5/">3.12.5/</a>                                            07-Aug-2024 11:36                   -
<a href="3.13.0/">3.13.0/</a>                                            05-Aug-2024 13:18                   -
<a href="3.14.0/">3.14.0/</a>                                            27-Jul-2024 13:19                   -
"""


class TestGetLatestPythonVersion(TestCase):
    maxDiff = None

    def test_extract_versions(self):
        self.assertEqual(
            extract_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.11'),
            ['3.11.9', '3.11.8', '3.11.7'],
        )
        self.assertEqual(
            extract_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.12'),
            ['3.12.5', '3.12.4', '3.12.3', '3.12.2', '3.12.1', '3.12.0'],
        )
        self.assertEqual(
            extract_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.13'),
            ['3.13.0'],
        )

    def test_get_latest_versions(self):
        self.assertEqual(get_latest_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.11'), '3.11.9')
        self.assertEqual(get_latest_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.12'), '3.12.5')
        self.assertEqual(get_latest_versions(html=PYTHON_ORG_FTP_HTML, major_version='3.13'), '3.13.0')

    def test_example_script(self):
        assert_is_file(EXAMPLE_SCRIPT_PATH)
        with tempfile.TemporaryDirectory(prefix='test_example_script') as temp_dir:
            temp_path = Path(temp_dir)

            # Copy EXAMPLE_SCRIPT_PATH into temp_dir:
            temp_script_path = temp_path / EXAMPLE_SCRIPT_PATH.name
            temp_script_path.write_text(EXAMPLE_SCRIPT_PATH.read_text())
            temp_script_path.chmod(0o755)

            # Add a fake Python interpreter:
            fake_python_path = temp_path / 'python3.12'
            fake_python_path.write_text(
                inspect.cleandoc(
                    """
                    #!/usr/bin/env python3
                    print("A fake Python 3.12.99")
                    """
                )
            )
            fake_python_path.chmod(0o755)

            # Check the fake python:
            self.assertEqual(
                subprocess.check_output(
                    [fake_python_path],
                    text=True,
                    stderr=subprocess.STDOUT,
                    cwd=temp_path,
                ),
                'A fake Python 3.12.99\n',
            )

            # Add a fake "install_python.py" file:
            fake_install_python_path = temp_path / 'install_python.py'
            fake_install_python_path.write_text(f'print("{fake_python_path}")')

            # Check fake "install_python.py":
            self.assertEqual(
                subprocess.check_output(
                    [sys.executable, fake_install_python_path],
                    text=True,
                    stderr=subprocess.STDOUT,
                    cwd=temp_path,
                ),
                f'{fake_python_path}\n',
            )

            # Let's run "install_python_example.sh":
            try:
                output = subprocess.check_output(
                    [temp_script_path],
                    text=True,
                    stderr=subprocess.STDOUT,
                    cwd=temp_path,
                )
            except subprocess.CalledProcessError as e:
                print(Rule(title='stdout'))
                print(e.stdout)
                print(Rule(title='stderr'))
                print(e.stderr)
                print(Rule())
                raise
        self.assertEqual(
            output,
            (
                f"Python 3.12 used from: '{temp_path}/python3.12'\n"
                f"+ {temp_path}/python3.12 -VV\n"
                "A fake Python 3.12.99\n"
            ),
        )


class IncludeInstallPythonTestCase(IncludeInstallPythonBaseTestCase):
    maxDiff = None

    def test_auto_update_install_python(self):
        self.assertIsNone(self.DESTINATION_PATH)
        self.assertEqual(SOURCE_PATH.name, 'install_python.py')

        with tempfile.TemporaryDirectory() as temp_dir:
            self.DESTINATION_PATH = Path(temp_dir) / 'test.py'

            with self.assertRaises(AssertionError) as cm:
                self.auto_update_install_python()

            self.assertIn('File does not exists', str(cm.exception))

            self.DESTINATION_PATH.write_text('OLD')
            self.assertFalse(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))

            with self.assertRaises(AssertionError) as cm:
                self.auto_update_install_python()
            self.assertIn(' updated, please commit ', str(cm.exception))

            self.assertTrue(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))

            result = self.auto_update_install_python()
            self.assertIsNone(result)
            self.assertTrue(filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH))
