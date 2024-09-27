"""
    CLI for usage
"""
import dataclasses
import logging
import sys

import rich_click as click
from cli_base.autodiscover import import_all_files
from cli_base.cli_tools.rich_utils import rich_traceback_install
from cli_base.cli_tools.version_info import print_version
from cli_base.tyro_commands import TyroCommandCli
from rich import print  # noqa
from rich.console import Console

from rich_click import RichGroup

import manageprojects
from manageprojects import constants


logger = logging.getLogger(__name__)


cli = TyroCommandCli()


# Register all click commands, just by import all files in this package:
import_all_files(package=__package__, init_file=__file__)


@cli.register
def version():
    """Print version and exit"""
    # Pseudo command, because the version always printed on every CLI call ;)
    sys.exit(0)


def main():
    print_version(manageprojects)

    rich_traceback_install()

    # Execute Click CLI:
    cli.run(
        prog='./cli.py',
        description=constants.CLI_EPILOG,
    )
