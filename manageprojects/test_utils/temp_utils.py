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
