from importlib.metadata import version

from manageprojects.utilities.log_utils import log_config


__version__ = version('manageprojects')


log_config(force=False)
