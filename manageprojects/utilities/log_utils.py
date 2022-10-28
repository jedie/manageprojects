import logging


def log_config(force=True, level=logging.DEBUG, format='%(asctime)s %(levelname)s | %(message)s'):
    logger = logging.getLogger('manageprojects')
    is_configured = logger.handlers and logger.level
    if force or not is_configured:
        logger.setLevel(level)

        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(format))

        logger.addHandler(ch)
