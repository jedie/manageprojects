import warnings

from cli_base.cli_tools.git import Git as NewGit
from cli_base.cli_tools.git import (  # noqa
    GitBinNotFoundError,
    GitError,
    GitTagInfo,
    GitTagInfos,
    NoGitRepoError,
    get_git_root,
)


class Git(NewGit):
    """
    DEPRECATED: Migrate to: cli_base.cli_tools.git.Git
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Migrate to: cli_base.cli_tools.git.Git !',
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
