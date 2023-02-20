import dataclasses
import subprocess
from typing import Callable, Optional, Union
from unittest.mock import patch

from bx_py_utils.test_utils.context_managers import MassContextManager


@dataclasses.dataclass
class Call:
    popenargs: Union[tuple, list]
    args: tuple
    kwargs: Optional[dict]


class FakeStdout:
    def __init__(self, *, stdout: str):
        self.stdout = stdout


class SimpleRunReturnCallback:
    """
    Helper to return the same output on every mocked subprocess.run() call.
    """

    def __init__(self, *, stdout: str):
        self.stdout = stdout

    def __call__(self, *args, **kwargs):
        return FakeStdout(stdout=self.stdout)


class MissingSubprocessCallMockCallback:
    def __call__(self, popenargs, *args, **kwargs):
        raise AttributeError(f'SubprocessCallMock needs a "return_callback" for "subprocess.run({popenargs})" usage!')


class SubprocessCallMock(MassContextManager):
    def __init__(self, return_callback: Optional[Callable] = None):
        if return_callback is None:
            return_callback = MissingSubprocessCallMockCallback()

        class CallHelper:
            def __init__(self, calls, return_callback=None):
                self.calls = calls
                self.return_callback = return_callback

            def __call__(self, popenargs, *args, **kwargs):
                self.calls.append(Call(popenargs, args, kwargs))
                if self.return_callback:
                    return self.return_callback(popenargs, args, kwargs)

        self.calls: list[Call] = []
        self.mocks = [
            patch.object(subprocess, 'call', CallHelper(self.calls)),
            patch.object(subprocess, 'run', CallHelper(self.calls, return_callback)),
        ]

    def get_popenargs(self, rstrip_paths: Optional[tuple] = None) -> list:
        if rstrip_paths:
            rstrip_paths = [str(item) for item in rstrip_paths if item]  # e.g.: Path -> str

        result = []
        for call in self.calls:
            if rstrip_paths:
                temp = []
                for arg in call.popenargs:
                    for rstrip_path in rstrip_paths:
                        if arg.startswith(rstrip_path):
                            arg = f'...{arg.removeprefix(rstrip_path)}'
                    temp.append(arg)

                result.append(temp)

            else:
                result.append(call.popenargs)

        return result
