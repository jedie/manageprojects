import logging
from pathlib import Path
from unittest import TestCase


class AssertLogs:
    """
    Capture and assert log output from different loggers.
    """

    def __init__(
        self,
        test_case: TestCase,
        loggers: tuple[str, ...] = ('manageprojects', 'cookiecutter'),
        level=logging.DEBUG,
    ):
        assertLogs = test_case.assertLogs

        self.logs = []
        for logger in loggers:
            self.logs.append(assertLogs(logger, level=level))

        self.context_managers = None

    def __enter__(self):
        self.context_managers = [log.__enter__() for log in self.logs]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for log in self.logs:
            log.__exit__(exc_type, exc_val, exc_tb)

    def assert_in(self, *test_parts):
        outputs = []
        for cm in self.context_managers:
            outputs.extend(cm.output)

        output = '\n'.join(outputs)
        for part in test_parts:
            if isinstance(part, Path):
                part = str(part)
            assert part in output, f'Log part {part!r} not found in:\n{output}'
