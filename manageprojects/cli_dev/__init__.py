"""
    CLI for development
"""

import importlib
import logging
import sys

from bx_py_utils.path import assert_is_file
from cli_base.autodiscover import import_all_files
from cli_base.cli_tools.dev_tools import run_coverage, run_nox, run_unittest_cli
from cli_base.cli_tools.version_info import print_version
import rich_click as click
from rich_click import RichGroup
from typeguard import install_import_hook

import manageprojects
from manageprojects import constants


# Check type annotations via typeguard in all tests.
# Sadly we must activate this here and can't do this in ./tests/__init__.py
install_import_hook(packages=('manageprojects',))

# reload the module, after the typeguard import hook is activated:
importlib.reload(manageprojects)


logger = logging.getLogger(__name__)


PACKAGE_ROOT = constants.BASE_PATH.parent
assert_is_file(PACKAGE_ROOT / 'pyproject.toml')  # Exists only in cloned git repo


class ClickGroup(RichGroup):  # FIXME: How to set the "info_name" easier?
    def make_context(self, info_name, *args, **kwargs):
        info_name = './dev-cli.py'
        return super().make_context(info_name, *args, **kwargs)


@click.group(
    cls=ClickGroup,
    epilog=constants.CLI_EPILOG,
)
def cli():
    pass


# Register all click commands, just by import all files in this package:
import_all_files(package=__package__, init_file=__file__)


@cli.command()
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)


def main():
    print_version(manageprojects)

    if len(sys.argv) >= 2:
        # Check if we can just pass a command call to origin CLI:
        command = sys.argv[1]
        command_map = {
            'test': run_unittest_cli,
            'nox': run_nox,
            'coverage': run_coverage,
        }
        if real_func := command_map.get(command):
            real_func(argv=sys.argv, exit_after_run=True)

    # Execute Click CLI:
    cli()
