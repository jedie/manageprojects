import warnings

import click
from cli_base.cli_tools.test_utils.rich_test_utils import NoColorEnvRich
from click.testing import CliRunner, Result


TERMINAL_WIDTH = 100


def subprocess_cli(*, cli_bin, args, exit_on_error=True):
    warnings.warn(
        'Migrate to: NoColorRichClickCli context manager !',
        DeprecationWarning,
        stacklevel=2,
    )
    from cli_base.cli_tools.test_utils.rich_click_test_utils import NoColorRichClickCli

    with NoColorRichClickCli() as cm:
        stdout = cm.invoke(cli_bin=cli_bin, args=args, exit_on_error=exit_on_error)
    return stdout


class ClickInvokeCliException(Exception):
    def __init__(self, result: Result):
        self.result = result


def invoke_click(cli, *args, expected_stderr='', expected_exit_code=0, strip=True, **kwargs):
    warnings.warn(
        'Deprecated: Will be removed in future !',
        DeprecationWarning,
        stacklevel=2,
    )
    assert isinstance(cli, click.Command)

    args = tuple([str(arg) for arg in args])  # e.g.: Path() -> str

    with NoColorEnvRich(width=TERMINAL_WIDTH):
        runner = CliRunner()
        result: Result = runner.invoke(cli=cli, args=args, **kwargs, color=False)

    if result.exception:
        raise ClickInvokeCliException(result) from result.exception

    stdout = result.stdout
    stderr = result.stderr
    assert stderr == expected_stderr, f'{stderr!r} is not {expected_stderr!r}'
    assert (
        result.exit_code == expected_exit_code
    ), f'Exit code {result.exit_code} is not {expected_exit_code}\n{stdout}\n{stderr}'

    if strip:
        stdout = '\n'.join(line.rstrip() for line in stdout.splitlines())
        stdout = stdout.strip()
    return stdout
