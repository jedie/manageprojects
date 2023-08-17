import warnings

from cli_base.cli_tools.test_utils.git_utils import init_git as new_init_git


def init_git2(*args, **kwargs):
    """
    DEPRECATED: Migrate to: cli_base.cli_tools.test_utils.git_utils.init_git !
    """
    warnings.warn(
        'Migrate to: cli_base.cli_tools.test_utils.git_utils.init_git !',
        DeprecationWarning,
        stacklevel=2,
    )
    new_init_git(*args, **kwargs)
