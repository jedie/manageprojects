import logging


def log_config(level=logging.DEBUG, format='%(asctime)s %(levelname)s | %(message)s'):
    logger = logging.getLogger('manageprojects')
    logger.setLevel(level)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(format))

    logger.addHandler(ch)
