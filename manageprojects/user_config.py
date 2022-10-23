import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def get_user_config_path() -> Path:
    if config_dir := os.environ.get('XDG_CONFIG_HOME'):
        config_path = Path(config_dir)
        if config_path.is_dir():
            return config_path

    config_path = Path.home() / '.config'
    if config_path.is_dir():
        return config_path

    config_path = Path.home() / 'Library' / 'Preferences'
    if config_path.is_dir():
        return config_path

    config_path = Path.home()
    logger.warning('Fallback user config path to: %s', config_path)
