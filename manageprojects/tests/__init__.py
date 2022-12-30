from manageprojects.utilities.log_utils import log_config


log_config(
    format='%(levelname)s %(name)s.%(funcName)s %(lineno)d | %(message)s',
    log_in_file=False,
    raise_log_output=True,
)
