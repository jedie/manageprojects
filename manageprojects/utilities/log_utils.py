import logging


def logger_setup(*, logger_name, force, level, format):
    logger = logging.getLogger(logger_name)
    is_configured = logger.handlers and logger.level
    if force or not is_configured:
        logger.setLevel(level)

        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(format))

        logger.addHandler(ch)


def log_config(
    force=True, level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s | %(message)s'
):
    logger_setup(logger_name='manageprojects', force=force, level=level, format=format)
    logger_setup(logger_name='cookiecutter', force=force, level=level, format=format)


def log_func_call(*, logger, func, **kwargs):
    func_name = func.__name__
    logger.debug('Call %r with: %r', func_name, kwargs)
    result = func(**kwargs)
    logger.debug('%r result: %r', func_name, result)
    return result
