import dataclasses
import datetime
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class CookiecutterResult:
    """
    Store information about a created Cookiecutter template
    """

    destination_path: Path
    git_path: Path
    git_hash: str
    commit_date: Optional[datetime.datetime]
    cookiecutter_context: dict

    def get_comment(self):
        if self.commit_date:
            return self.commit_date.isoformat()
        return ''


@dataclasses.dataclass
class ManageProjectsMeta:
    """
    Information about 'manageprojects' git hashes
    """

    initial_revision: Optional[str]
    initial_date: Optional[datetime.datetime]
    applied_migrations: list[str]
    cookiecutter_template: Optional[str]  # CookieCutter Template path or GitHub url
    cookiecutter_directory: Optional[str]  # Directory name of the CookieCutter Template
    cookiecutter_context: Optional[dict]

    def get_last_git_hash(self) -> str:
        """
        Get the lash git hash from 'pyproject.toml' file.
        """
        if self.applied_migrations:
            return self.applied_migrations[-1]
        return self.initial_revision
