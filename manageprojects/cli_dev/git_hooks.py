from manageprojects.cli_dev import PACKAGE_ROOT, cli
from manageprojects.format_file import ToolsExecutor


@cli.command()
def git_hooks():
    """
    Setup our "pre-commit" git hooks
    """
    executor = ToolsExecutor(cwd=PACKAGE_ROOT)
    executor.verbose_check_call('pre-commit', 'install')


@cli.command()
def run_git_hooks():
    """
    Run the installed "pre-commit" git hooks
    """
    executor = ToolsExecutor(cwd=PACKAGE_ROOT)
    executor.verbose_check_call('pre-commit', 'run', '--verbose', exit_on_error=True)
