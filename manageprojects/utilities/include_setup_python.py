import filecmp
from pathlib import Path
from unittest import TestCase

from bx_py_utils.path import assert_is_dir, assert_is_file

import manageprojects


SOURCE_PATH = Path(manageprojects.__file__).parent / 'setup_python.py'


class IncludeSetupPythonBaseTestCase(TestCase):
    """DocWrite: setup_python.md ## Include in own projects
    There is a unittest base class to include `setup_python.py` script in your project.
    If will check if the file is up2date and if not, it will update it.

    Just include `manageprojects` as a dev dependency in your project.
    And add a test like this:

    ```python
    class IncludeSetupPythonTestCase(IncludeSetupPythonBaseTestCase):

        # Set the path where the `setup_python.py` should be copied to:
        DESTINATION_PATH = Path(your_package.__file__).parent) / 'setup_python.py'

        # The test will pass, if the file is up2date, if it's update the script!
        def test_setup_python_is_up2date(self):
            self.auto_update_setup_python()
    ```

    Feel free to do it in a completely different way, this is just a suggestion ;)
    """

    DESTINATION_PATH: Path = None  # must be set in the subclass

    def auto_update_setup_python(self):
        assert_is_file(SOURCE_PATH)

        self.assertIsInstance(
            self.DESTINATION_PATH,
            Path,
            'Please set the "DESTINATION_PATH" in the subclass',
        )
        self.assertEqual(self.DESTINATION_PATH.suffix, '.py')
        assert_is_dir(self.DESTINATION_PATH.parent)

        self.assertTrue(
            self.DESTINATION_PATH.is_file(),
            f'File does not exists: "{self.DESTINATION_PATH}"\n(Please add at least a empty file there!)',
        )

        if filecmp.cmp(SOURCE_PATH, self.DESTINATION_PATH, shallow=False):
            # Files are equal -> nothing to do
            return

        self.DESTINATION_PATH.write_text(SOURCE_PATH.read_text())
        self.DESTINATION_PATH.chmod(0o775)  # Make it executable
        self.fail(f'File "{self.DESTINATION_PATH}" was updated, please commit the changes')
