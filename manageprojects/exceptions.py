class ProjectNotFound(FileNotFoundError):
    pass


class NoManageprojectsMeta(Exception):
    """
    A existing 'pyproject.toml' file does not contain [manageprojects] information
    """

    pass
