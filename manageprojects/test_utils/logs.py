import warnings

from cli_base.cli_tools.test_utils.logs import AssertLogs as OriginalAssertLogs


class AssertLogs(OriginalAssertLogs):
    """
    Capture and assert log output from different loggers.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Migrate to: cli_base.cli_tools.test_utils.logs.AssertLogs !',
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
