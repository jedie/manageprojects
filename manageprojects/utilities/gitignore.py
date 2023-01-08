import logging
from functools import lru_cache
from pathlib import Path

from pathspec import GitIgnoreSpec, PathSpec


logger = logging.getLogger(__name__)


@lru_cache
def get_gitignore(root: Path) -> PathSpec:
    gitignore = root / '.gitignore'

    lines = []
    if gitignore.is_file():
        with gitignore.open(encoding='utf-8') as f:
            lines = f.readlines()
    else:
        print(f'WARNING: No .gitignore found in {root}')

    return GitIgnoreSpec.from_lines(lines)
