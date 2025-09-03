from cli_base.cli_tools.code_style import assert_code_style
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE
import rich_click as click

from manageprojects.cli_dev import PACKAGE_ROOT, cli


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def lint(verbosity: int):
    """
    Check/fix code style by run: "ruff check --fix"
    """
    assert_code_style(package_root=PACKAGE_ROOT, verbose=bool(verbosity), sys_exit=True)
