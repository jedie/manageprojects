import logging
import platform
import sys
from pathlib import Path

import typer
from cookiecutter.exceptions import RepositoryNotFound
from cookiecutter.main import cookiecutter
from rich import print  # noqa

import manageprojects
from manageprojects.git import Git, get_git_root
from manageprojects.log_utils import log_config
from manageprojects.path_utils import assert_is_dir
from manageprojects.subprocess_utils import verbose_check_call

logger = logging.getLogger(__name__)


BASE_PATH = Path(manageprojects.__file__).parent
PROJECT_TEMPLATE_PATH = BASE_PATH / 'project_templates'
assert_is_dir(PROJECT_TEMPLATE_PATH)


cli = typer.Typer()


def which(file_name: str) -> Path:
    venv_bin_path = Path(sys.executable).parent
    assert venv_bin_path.is_dir()
    bin_path = venv_bin_path / file_name
    if not bin_path.is_file():
        raise FileNotFoundError(f'File {file_name}!r not found in {venv_bin_path}')
    return bin_path


@cli.command()
def mypy():
    """Run Mypy (configured in pyproject.toml)"""
    verbose_check_call(which('mypy'), '.')


@cli.command()
def test():
    verbose_check_call(sys.executable, '-m', 'pytest')


@cli.command()
def coverage():
    """
    Run and show coverage.
    """
    coverage_bin = which('coverage')
    verbose_check_call(coverage_bin, 'run', '-m', 'pytest')
    verbose_check_call(coverage_bin, 'html')
    if platform.system() == 'Darwin':
        verbose_check_call('open', 'htmlcov/index.html')
    elif platform.system() == 'Linux' and 'Microsoft' in platform.release():  # on WSL
        verbose_check_call('explorer.exe', r'htmlcov\index.html')


@cli.command()
def update():
    """
    Update the development environment by calling:
    - pip-compile production.in develop.in -> develop.txt
    - pip-compile production.in -> production.txt
    - pip-sync develop.txt
    """
    base_command = [
        which('pip-compile'),
        '--verbose',
        '--upgrade',
        '--allow-unsafe',
        '--generate-hashes',
        'requirements/production.in',
    ]
    verbose_check_call(  # develop + production
        *base_command,
        'requirements/develop.in',
        '--output-file',
        'requirements/develop.txt',
    )
    verbose_check_call(  # production only
        *base_command,
        '--output-file',
        'requirements/production.txt',
    )
    verbose_check_call(which('pip-sync'), 'requirements/develop.txt')


@cli.command()
def version():
    """Print version and exit"""
    print('manageprojects v', end='')
    from manageprojects import __version__

    print(__version__, end=' ')

    git = Git(cwd=get_git_root(path=BASE_PATH))
    current_hash = git.get_current_hash(verbose=False)
    print(current_hash)


@cli.command()
def start_project(template: str, destination: Path):
    """
    Start a new project via a CookieCutter Template
    """
    print(f'Start project with template: {template!r}')
    template_path = PROJECT_TEMPLATE_PATH / template
    if template_path.is_dir():
        directory = str(template_path)
        logging.info(f'Use own template: {template}')
    else:
        logging.info(f'Assume it is a external template: {template}')
        directory = None

    print(f'Destination: {destination}')
    if destination.exists():
        print(f'Error: Destination "{destination}" already exists')
        sys.exit(1)
    if not destination.parent.is_dir():
        print(f'Error: Destination parent "{destination.parent}" does not exists')
        sys.exit(1)

    cookiecutter_kwargs = dict(
        template=template, replay=True, directory=directory, output_dir=destination
    )
    logging.debug('Call cookiecutter with: %r', cookiecutter_kwargs)
    try:
        cookiecutter(**cookiecutter_kwargs)
    except RepositoryNotFound as err:
        print(f'Error: {err}')
        print('Existing templates are:')
        print([item.name for item in PROJECT_TEMPLATE_PATH.iterdir() if item.is_dir()])
        sys.exit(1)


def main():
    log_config()
    cli()
