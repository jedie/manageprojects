import dataclasses
import subprocess
from pathlib import Path
from typing import Optional, Union
from unittest.mock import patch


@dataclasses.dataclass
class Call:
    popenargs: Union[tuple, list]
    args: tuple
    kwargs: Optional[dict]


class SubprocessCallMock:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        self.m = patch.object(subprocess, 'call', self)
        self.m.__enter__()
        return self

    def __call__(self, popenargs, *args, **kwargs):
        self.calls.append(Call(popenargs, args, kwargs))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.m.__exit__(exc_type, exc_val, exc_tb)

    def get_popenargs(self, rstrip_path: Optional[Path] = None):
        if isinstance(rstrip_path, Path):
            rstrip_path = str(rstrip_path)

        result = []
        for call in self.calls:
            if rstrip_path:
                temp = []
                for arg in call.popenargs:
                    if arg.startswith(rstrip_path):
                        arg = f'...{arg.removeprefix(rstrip_path)}'
                    temp.append(arg)

                result.append(temp)

            else:
                result.append(call.popenargs)

        return result
