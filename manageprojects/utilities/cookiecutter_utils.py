import logging


logger = logging.getLogger(__name__)


class CookieCutterHookHandler:
    """
    Capture the effective Cookiecutter Template Context via injecting the Cookiecutter hooks.
    """

    def __init__(self, origin_run_hook):
        self.origin_run_hook = origin_run_hook
        self.context = {}

    def __call__(self, hook_name, project_dir, context):
        logger.debug('Hook %r for %r context: %r', hook_name, project_dir, context)
        origin_hook_result = self.origin_run_hook(hook_name, project_dir, context)
        self.context.update(context)
        return origin_hook_result
