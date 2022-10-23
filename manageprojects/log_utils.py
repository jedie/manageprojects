import logging


def log_config():
    logging.basicConfig(format='%(asctime)s %(levelname)s | %(message)s', level=logging.DEBUG)
