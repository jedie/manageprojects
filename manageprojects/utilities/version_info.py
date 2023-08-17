import warnings

from cli_base.cli_tools.version_info import print_version as new_print_version


def print_version(*args, **kwargs) -> None:
    """
    DEPRECATED: Migrate to: cli_base.cli_tools.version_info.print_version !
    """
    warnings.warn(
        'Migrate to: cli_base.cli_tools.version_info.print_version !',
        DeprecationWarning,
        stacklevel=2,
    )
    new_print_version(*args, **kwargs)
