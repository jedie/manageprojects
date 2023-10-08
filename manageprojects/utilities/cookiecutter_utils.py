import logging

from cookiecutter.generate import generate_files


logger = logging.getLogger(__name__)


class GenerateFilesWrapper:
    """
    Capture the effective Cookiecutter Template Context
    """

    def __init__(self):
        self.context = None

    def __call__(self, **kwargs):
        logger.debug('GenerateFilesWrapper called with: %s', kwargs)
        self.context = kwargs['context']
        return generate_files(**kwargs)
