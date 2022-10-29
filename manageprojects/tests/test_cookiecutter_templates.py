from pathlib import Path

from bx_py_utils.test_utils.datetime import parse_dt
from bx_py_utils.test_utils.snapshot import assert_text_snapshot

from manageprojects.data_classes import CookiecutterResult, ManageProjectsMeta
from manageprojects.exceptions import NoManageprojectsMeta, ProjectNotFound
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.pyproject_toml import parse_pyproject_toml, update_pyproject_toml
from manageprojects.utilities.temp_path import TemporaryDirectory


class CookieCutterTemplatesTestCase(BaseTestCase):
    def test_pyproject_toml_utils(self):
        with self.assertRaises(ProjectNotFound):
            parse_pyproject_toml(path=Path('/does/not/exists/'))

        with TemporaryDirectory(prefix='test_update_pyproject_toml_') as temp_path:
            pyproject_toml_path = temp_path / 'pyproject.toml'

            pyproject_toml_path.touch()
            with self.assertRaises(NoManageprojectsMeta):
                parse_pyproject_toml(pyproject_toml_path)

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0001',
                    commit_date=parse_dt('2000-01-01T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                    }
                },
            )
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertIsInstance(meta, ManageProjectsMeta)
            self.assertEqual(
                meta,
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+00:00'),
                    applied_migrations=[],
                ),
            )
            self.assertEqual(meta.get_last_git_hash(), 'abc0001')

            # Insert "prefix" user data into 'pyproject.toml':
            origin = pyproject_toml_path.read_text()
            new = f'[project]\nname = "foo bar"\n\n\n{origin}'
            pyproject_toml_path.write_text(new)

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0002',
                    commit_date=parse_dt('2000-02-02T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002'],
                    },
                },
            )
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertEqual(meta.get_last_git_hash(), 'abc0002')

            # Append "suffix" user data into 'pyproject.toml':
            origin = pyproject_toml_path.read_text()
            new = f'{origin}\n\n[foo]\nbar = 1\n'
            pyproject_toml_path.write_text(new)

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0003',
                    commit_date=None,  # No: commit_date
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002', 'abc0003'],
                    },
                    'foo': {'bar': 1},  # suffix user data
                },
            )
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertEqual(meta.get_last_git_hash(), 'abc0003')

            update_pyproject_toml(
                result=CookiecutterResult(
                    destination_path=temp_path,
                    git_path=temp_path / 'foo' / 'bar',  # not relevant here
                    git_hash='abc0004',
                    commit_date=parse_dt('2000-04-04T00:00:00+0000'),
                    pyproject_toml_path=pyproject_toml_path,
                )
            )
            self.assert_tomli(
                pyproject_toml_path,
                {
                    'project': {'name': 'foo bar'},  # prefix user data
                    'manageprojects': {
                        'initial_revision': 'abc0001',
                        'initial_date': '2000-01-01T00:00:00+00:00',
                        'applied_migrations': ['abc0002', 'abc0003', 'abc0004'],
                    },
                    'foo': {'bar': 1},  # suffix user data
                },
            )
            self.assertEqual(
                parse_pyproject_toml(pyproject_toml_path),
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+00:00'),
                    applied_migrations=['abc0002', 'abc0003', 'abc0004'],
                ),
            )
            meta = parse_pyproject_toml(pyproject_toml_path)
            self.assertEqual(meta.get_last_git_hash(), 'abc0004')

            assert_text_snapshot(got=pyproject_toml_path.read_text())
