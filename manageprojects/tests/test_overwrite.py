import inspect
import json
from pathlib import Path

from bx_py_utils.path import assert_is_file
from bx_py_utils.test_utils.redirect import RedirectOut
from cli_base.cli_tools.test_utils.git_utils import init_git
from cli_base.cli_tools.test_utils.logs import AssertLogs

from manageprojects.cookiecutter_templates import update_managed_project
from manageprojects.data_classes import ManageProjectsMeta, OverwriteResult
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.pyproject_toml import PyProjectToml
from manageprojects.utilities.temp_path import TemporaryDirectory


class UpdateByOverwriteTestCase(BaseTestCase):
    def test_happy_path(self):
        cookiecutter_context = {
            'dir_name': 'a_directory',
            'file_name': 'a_file_name',
            'value': 'FooBar',
        }
        context = {'cookiecutter': cookiecutter_context}

        with TemporaryDirectory(prefix='test_update_by_overwrite_') as main_temp_path:
            project_path = main_temp_path / 'project_path'
            dst_file_path = project_path / 'a_file_name.py'

            template_path = main_temp_path / 'template'
            template_dir_name = 'template_dir'
            template_dir_path = template_path / template_dir_name
            config_file_path = template_dir_path / 'cookiecutter.json'

            test_file_path = template_dir_path / '{{cookiecutter.dir_name}}' / '{{cookiecutter.file_name}}.py'

            dst_file_path.parent.mkdir(parents=True)
            dst_file_path.write_text('# This is a test line, not changed')

            config_file_path.parent.mkdir(parents=True)
            config_file_path.write_text(json.dumps(cookiecutter_context))

            project_git, project_from_rev = init_git(project_path, comment='Git init project.')
            dst_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 1
                    #
                    # The same cookiecutter value:
                    print('Test: FooBar')
                    '''
                )
            )
            project_git.add('.')
            project_git.commit('Store revision 1')

            test_file_path.parent.mkdir(parents=True)
            test_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 1
                    #
                    # The same cookiecutter value:
                    print('Test: {{ cookiecutter.value }}')
                    '''
                )
            )

            git, from_rev = init_git(template_path, comment='Git init template.')
            from_date = git.get_commit_date(verbose=False)

            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=project_path)
                toml.init(
                    revision=from_rev,
                    dt=from_date,
                    template=str(template_path),
                    directory=template_dir_name,
                )
            logs.assert_in('Create new pyproject.toml')
            toml.create_or_update_cookiecutter_context(context=context)
            toml.save()
            toml_content = toml.path.read_text()
            self.assertIn('# Created by manageprojects', toml_content)
            self.assertIn('[manageprojects] # https://github.com/jedie/manageprojects', toml_content)
            self.assertIn(f'initial_revision = "{from_rev}"', toml_content)
            self.assertIn(f'cookiecutter_template = "{template_path}"', toml_content)
            self.assertIn('cookiecutter_directory = "template_dir"', toml_content)

            test_file_path.write_text(
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 2
                    #
                    # The same cookiecutter value:
                    print('Test: {{ cookiecutter.value }}')
                    '''
                )
            )
            Path(template_dir_path, '{{cookiecutter.dir_name}}', 'a_new_file.txt').touch()
            new_file2 = Path(template_dir_path, '{{cookiecutter.dir_name}}', 'new_dir1', 'new_dir2', 'a_file.txt')
            new_file2.parent.mkdir(parents=True)
            new_file2.touch()

            git.add('.', verbose=False)
            git.commit('Template rev 2', verbose=False)
            to_rev = git.get_current_hash(verbose=False)
            to_date = git.get_commit_date(verbose=False)
            assert to_date

            patch_file_path = Path(
                main_temp_path,
                'repo_path',
                '.manageprojects',
                'patches',
                f'{from_rev}_{to_rev}.patch',
            )
            self.assertFalse(patch_file_path.exists())

            # Don't overwrite if destination project git is not clean:
            with RedirectOut() as buffer:
                with self.assertRaises(SystemExit), AssertLogs(self):
                    update_managed_project(
                        project_path=project_path,
                        overwrite=True,  # Update by overwrite
                        password=None,
                        config_file=config_file_path,
                        cleanup=False,  # Keep temp files if this test fails, for better debugging
                        input=False,  # No user input in tests ;)
                    )
            self.assertIn('Abort', buffer.stderr)
            self.assertIn('is not clean', buffer.stderr)
            self.assertIn('?? pyproject.toml', buffer.stdout)

            # Make project git "clean":
            project_git.add('.', verbose=False)
            project_git.commit('add pyproject.toml', verbose=False)

            with RedirectOut() as buffer:
                with AssertLogs(self) as logs:
                    result = update_managed_project(
                        project_path=project_path,
                        overwrite=True,  # Update by overwrite
                        password=None,
                        config_file=config_file_path,
                        cleanup=False,  # Keep temp files if this test fails, for better debugging
                        input=False,  # No user input in tests ;)
                    )
            self.assertEqual(buffer.stderr, '')
            self.assertIn('Update by overwrite', buffer.stdout)
            self.assertIn('UPDATE file', buffer.stdout)
            self.assertIn('NEW file', buffer.stdout)

            self.assert_file_content(
                dst_file_path,
                inspect.cleandoc(
                    '''
                    # This is a test line, not changed
                    #
                    # Revision 2
                    #
                    # The same cookiecutter value:
                    print('Test: FooBar')
                    '''
                ),
            )
            assert_is_file(path=Path(project_path, 'a_new_file.txt'))
            assert_is_file(path=Path(project_path, 'new_dir1', 'new_dir2', 'a_file.txt'))

            self.assertIsInstance(result, OverwriteResult)
            self.assertEqual(
                result,
                OverwriteResult(
                    to_rev=to_rev,
                    to_commit_date=to_date,
                ),
            )

            # Check updated toml file:
            with AssertLogs(self, loggers=('manageprojects',)) as logs:
                toml = PyProjectToml(project_path=project_path)
                mp_meta: ManageProjectsMeta = toml.get_mp_meta()
            logs.assert_in('Read existing pyproject.toml')
            self.assertEqual(mp_meta.initial_revision, from_rev)
            self.assertEqual(mp_meta.applied_migrations, [to_rev])
            content = toml.dumps()
            self.assertIn('[manageprojects] # https://github.com/jedie/manageprojects', content)
