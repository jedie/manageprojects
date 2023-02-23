import sys
from pathlib import Path


INITIAL_REVISION = 'initial_revision'
INITIAL_DATE = 'initial_date'
APPLIED_MIGRATIONS = 'applied_migrations'
COOKIECUTTER_TEMPLATE = 'cookiecutter_template'
COOKIECUTTER_DIRECTORY = 'cookiecutter_directory'
COOKIECUTTER_CONTEXT = 'cookiecutter_context'

CLI_EPILOG = 'Project Homepage: https://github.com/jedie/manageprojects'

# Draker has some troubles fixing new lines,
# so just call autopep8 with following selection before call darker:
FORMAT_PY_FILE_DARKER_PRE_FIXES = ','.join(
    sorted(
        [
            'E301',  # expected 1 blank line
            'E302',  # expected 2 blank lines
            'E303',  # too many blank lines
            'W391',  # blank line at end of file
            'E305',  # expected 2 blank lines after class or function definition
        ]
    )
)
FORMAT_PY_FILE_DEFAULT_MIN_PYTON_VERSION = '3.9'
FORMAT_PY_FILE_DEFAULT_MAX_LINE_LENGTH = 119

PY_BIN_PATH = Path(sys.executable).parent
