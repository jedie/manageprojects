import logging
from pathlib import Path

from rich import print  # noqa

from manageprojects.git import Git


logger = logging.getLogger(__name__)


def _print_version(module, project_root: Path = None):
    print(f'[bold][green]{module.__name__}[/green] v', end='')
    print(module.__version__, end=' ')

    if not project_root:
        project_root = Path(module.__file__).parent.parent
    git_path = project_root / '.git'
    if git_path.is_dir():
        git = Git(cwd=git_path)
        current_hash = git.get_current_hash(verbose=False)
        print(f'[blue]{current_hash}[/blue]', end=' ')
        print(f'([white]{git.cwd}[/white])')
    else:
        print(f'(No git found for: {project_root})')


def print_version(module, project_root: Path = None) -> None:
    try:
        _print_version(module=module, project_root=project_root)
    except Exception as err:
        logger.exception('Error print version: %s', err)

        # Catch all errors, otherwise the CLI is not usable ;)
        print(f'{module} (print version error: {err})')
