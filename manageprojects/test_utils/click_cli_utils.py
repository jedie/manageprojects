import click
from bx_py_utils.path import assert_is_file
from click.testing import CliRunner

from manageprojects.tests.base import ForceRichTerminalWidth
from manageprojects.utilities.subprocess_utils import verbose_check_output


def subprocess_cli(*, cli_bin, args, exit_on_error=True):
    assert_is_file(cli_bin)
    return verbose_check_output(cli_bin, *args, cwd=cli_bin.parent, exit_on_error=exit_on_error)


def invoke_click(cli, *args, expected_stderr='', expected_exit_code=0, **kwargs):
    assert isinstance(cli, click.Command)

    args = tuple([str(arg) for arg in args])  # e.g.: Path() -> str

    with ForceRichTerminalWidth():
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(cli=cli, args=args, **kwargs, color=False)

    stdout = result.stdout
    stderr = result.stderr
    assert stderr == expected_stderr, f'{stderr!r} is not {expected_stderr!r}'
    assert (
        result.exit_code == expected_exit_code
    ), f'Exit code {result.exit_code} is not {expected_exit_code}\n{stdout}\n{stderr}'

    return stdout
