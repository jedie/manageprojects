import logging

from cookiecutter.generate import generate_files

from manageprojects.utilities.log_utils import log_func_call


logger = logging.getLogger(__name__)


def cookiecutter_generate_files(
    *,
    repo_dir,
    replay_context,
    output_dir,
    overwrite_if_exists=True,
    skip_if_file_exists=False,
):
    project_dir = log_func_call(
        logger=logger,
        func=generate_files,
        repo_dir=repo_dir,
        context=replay_context,
        output_dir=output_dir,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    )
    return project_dir
