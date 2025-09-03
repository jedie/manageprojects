import logging
import tempfile

from bx_py_utils.pyproject_toml import get_pyproject_config
from cli_base.cli_tools.dev_tools import run_unittest_cli
from cli_base.cli_tools.subprocess_utils import ToolsExecutor
from cli_base.cli_tools.verbosity import OPTION_KWARGS_VERBOSE, setup_logging
import click

import manageprojects
from manageprojects.cli_dev import PACKAGE_ROOT, cli
from manageprojects.utilities.publish import build as publish_build
from manageprojects.utilities.publish import publish_package


logger = logging.getLogger(__name__)


@cli.command()
def install():
    """
    Install requirements and 'manageprojects' via pip as editable.
    """
    tools_executor = ToolsExecutor(cwd=PACKAGE_ROOT)
    tools_executor.verbose_check_call('uv', 'sync')
    tools_executor.verbose_check_call('pip', 'install', '--no-deps', '-e', '.')


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def build(verbosity: int):
    """
    Build the manageproject (More a test of manageprojects.utilities.publish.build)
    """
    setup_logging(verbosity=verbosity)
    publish_build(PACKAGE_ROOT)


def run_pip_audit(verbosity: int):
    tools_executor = ToolsExecutor(cwd=PACKAGE_ROOT)

    with tempfile.NamedTemporaryFile(prefix='requirements', suffix='.txt') as temp_file:
        tools_executor.verbose_check_call(
            'uv',
            'export',
            '--no-header',
            '--frozen',
            '--no-editable',
            '--no-emit-project',
            '-o',
            temp_file.name,
        )

        config: dict = get_pyproject_config(
            section=('tool', 'cli_base', 'pip_audit'),
            base_path=PACKAGE_ROOT,
        )
        logger.debug('pip_audit config: %r', config)
        assert isinstance(config, dict), f'Expected a dict: {config=}'

        popenargs = ['pip-audit', '--strict', '--require-hashes']

        if verbosity:
            popenargs.append(f'-{"v" * verbosity}')

        for vulnerability_id in config.get('ignore-vuln', []):
            popenargs.extend(['--ignore-vuln', vulnerability_id])

        popenargs.extend(['-r', temp_file.name])

        logger.debug('pip_audit args: %s', popenargs)
        tools_executor.verbose_check_call(*popenargs)


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def pip_audit(verbosity: int):
    """
    Run pip-audit check against current requirements files
    """
    setup_logging(verbosity=verbosity)
    run_pip_audit(verbosity=verbosity)


@cli.command()
@click.option('-v', '--verbosity', **OPTION_KWARGS_VERBOSE)
def update(verbosity: int):
    """
    Update dependencies (uv.lock) and git pre-commit hooks
    """
    setup_logging(verbosity=verbosity)

    tools_executor = ToolsExecutor(cwd=PACKAGE_ROOT)

    tools_executor.verbose_check_call('pip', 'install', '-U', 'pip')
    tools_executor.verbose_check_call('pip', 'install', '-U', 'uv')
    tools_executor.verbose_check_call('uv', 'lock', '--upgrade')

    run_pip_audit(verbosity=verbosity)

    # Install new dependencies in current .venv:
    tools_executor.verbose_check_call('uv', 'sync')

    # Update git pre-commit hooks:
    tools_executor.verbose_check_call('pre-commit', 'autoupdate')


@cli.command()
def publish():
    """
    Build and upload this project to PyPi
    """
    run_unittest_cli(verbose=False, exit_after_run=False)  # Don't publish a broken state

    publish_package(module=manageprojects, package_path=PACKAGE_ROOT)
