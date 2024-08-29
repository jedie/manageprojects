import dataclasses
import datetime
from pathlib import Path


@dataclasses.dataclass
class CookiecutterResult:
    """
    Store information about a created Cookiecutter template
    """

    destination_path: Path
    git_path: Path
    git_hash: str
    commit_date: datetime.datetime | None
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

    initial_revision: str
    initial_date: datetime.datetime
    applied_migrations: list[str]
    cookiecutter_template: str | None  # CookieCutter Template path or GitHub url
    cookiecutter_directory: str | None  # Directory name of the CookieCutter Template
    cookiecutter_context: dict | None

    def get_last_git_hash(self) -> str:
        """
        Get the lash git hash from 'pyproject.toml' file.
        """
        if self.applied_migrations:
            return self.applied_migrations[-1]
        return self.initial_revision


@dataclasses.dataclass
class ResultBase:
    to_rev: str
    to_commit_date: datetime.datetime


@dataclasses.dataclass
class GenerateTemplatePatchResult(ResultBase):
    repo_path: Path  # Cookiecutter template path
    patch_file_path: Path

    from_rev: str
    compiled_from_path: Path

    compiled_to_path: Path


@dataclasses.dataclass
class OverwriteResult(ResultBase):
    pass
