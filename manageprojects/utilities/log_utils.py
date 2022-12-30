import atexit
import logging
import tempfile

from bx_py_utils.test_utils.log_utils import RaiseLogUsage


def logger_setup(*, logger_name, level, format, log_filename, raise_log_output):
    logger = logging.getLogger(logger_name)
    is_configured = logger.handlers and logger.level
    if not is_configured:
        logger.setLevel(level)

        if raise_log_output:
            handler = RaiseLogUsage()
        elif log_filename:
            handler = logging.FileHandler(filename=log_filename)
        else:
            handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(format))

        logger.addHandler(handler)


def print_log_info(filename):
    print(f'\nLog file created here: {filename}\n')


def log_config(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s.%(funcName)s %(lineno)d | %(message)s',
    log_in_file=True,
    raise_log_output=False,
):
    if log_in_file:
        log_file = tempfile.NamedTemporaryFile(
            prefix='manageprojects_', suffix='.log', delete=False
        )
        log_filename = log_file.name
    else:
        log_filename = None

    logger_setup(
        logger_name='manageprojects',
        level=level,
        format=format,
        log_filename=log_filename,
        raise_log_output=raise_log_output,
    )
    logger_setup(
        logger_name='cookiecutter',
        level=level,
        format=format,
        log_filename=log_filename,
        raise_log_output=raise_log_output,
    )

    if log_filename:
        atexit.register(print_log_info, log_filename)


def log_func_call(*, logger, func, **kwargs):
    func_name = func.__name__
    logger.debug('Call %r with: %r', func_name, kwargs)
    result = func(**kwargs)
    logger.debug('%r result: %r', func_name, result)
    return result
