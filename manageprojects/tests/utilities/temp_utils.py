import shutil
import tempfile
from pathlib import Path


class TempContentFile:
    def __init__(self, content, prefix=None, suffix=None):
        self.content = content
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self) -> Path:
        self.tmp = tempfile.NamedTemporaryFile(prefix=self.prefix, suffix=self.suffix)
        self.tmp.__enter__()
        file_path = Path(self.tmp.name)
        file_path.write_text(self.content)
        return file_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tmp.__exit__(exc_type, exc_val, exc_tb)


class TemporaryDirectory:
    """
    Similar to origin tempfile.TemporaryDirectory, but:
     * cleanup only if no error happens
     * returns a Path object
    """

    def __init__(self, prefix=None, suffix=None, dir=None):
        self.prefix = prefix
        self.suffix = suffix
        self.dir = dir

    def __enter__(self) -> Path:
        temp_name = tempfile.mkdtemp(prefix=self.prefix, suffix=self.suffix, dir=self.dir)
        self.temp_path = Path(temp_name)
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"no cleanup of {self.temp_path}, cause: {exc_val}")
            return False

        shutil.rmtree(self.temp_path)
