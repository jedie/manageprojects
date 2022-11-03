import logging
import shutil
import tempfile
from pathlib import Path


logger = logging.getLogger(__name__)


class TemporaryDirectory:
    """
    Similar to origin tempfile.TemporaryDirectory, but:
     * cleanup only if no error happens
     * returns a Path object
    """

    def __init__(self, prefix=None, suffix=None, dir=None, cleanup=True):
        self.prefix = prefix
        self.suffix = suffix
        self.dir = dir
        self.cleanup = cleanup

    def __enter__(self) -> Path:
        temp_name = tempfile.mkdtemp(prefix=self.prefix, suffix=self.suffix, dir=self.dir)
        self.temp_path = Path(temp_name)
        return self.temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.exception(f"no cleanup of {self.temp_path}, cause: {exc_val}")
            return False

        if self.cleanup:
            shutil.rmtree(self.temp_path)
        else:
            logger.warning('No temp files cleanup for: %s', self.temp_path)
