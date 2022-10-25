import logging

from cookiecutter.main import cookiecutter


logger = logging.getLogger(__name__)


def run_cookiecutter(**cookiecutter_kwargs):
    logger.debug("Call cookiecutter with: %r", cookiecutter_kwargs)
    cookiecutter(**cookiecutter_kwargs)
