import argparse
from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import patch

from bx_py_utils.doc_write.data_structures import MacroContext
from bx_py_utils.path import assert_is_file

from manageprojects import setup_python
from manageprojects.setup_python import LASTEST_RELEASE_URL


PROG = Path(setup_python.__file__).name
EXAMPLE_SCRIPT_PATH = Path(setup_python.__file__).parent / 'setup_python_example.sh'


class HelpFormatterMock(argparse.ArgumentDefaultsHelpFormatter):

    def __init__(self, *args, **kwargs):
        kwargs['width'] = 120
        kwargs['prog'] = PROG  # Force: 'setup_python.py'
        super().__init__(*args, **kwargs)


def help(macro_context: MacroContext):
    yield '```shell'
    yield f'$ python3 {PROG} --help\n'
    with patch.object(argparse, 'ArgumentDefaultsHelpFormatter', HelpFormatterMock):
        parser: ArgumentParser = setup_python.get_parser()
        yield parser.format_help()
    yield '```'


def example_shell_script(macro_context: MacroContext):
    assert_is_file(EXAMPLE_SCRIPT_PATH)

    yield '```shell'
    yield EXAMPLE_SCRIPT_PATH.read_text()
    yield '```'


def lastest_release_url(macro_context: MacroContext):
    yield LASTEST_RELEASE_URL


def optimization_priority(macro_context: MacroContext):
    yield ''
    for number, optimization in enumerate(setup_python.OPTIMIZATION_PRIORITY, 1):
        yield f'{number}. `{optimization}`'
