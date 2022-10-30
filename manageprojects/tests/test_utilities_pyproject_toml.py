import inspect

import tomlkit
from bx_py_utils.test_utils.datetime import parse_dt

from manageprojects.data_classes import ManageProjectsMeta
from manageprojects.tests.base import BaseTestCase
from manageprojects.utilities.pyproject_toml import PyProjectToml, add_or_update_nested_dict
from manageprojects.utilities.temp_path import TemporaryDirectory


class PyProjectTomlTestCase(BaseTestCase):
    maxDiff = None

    def test_dict2table(self):
        doc = tomlkit.document()
        add_or_update_nested_dict(
            doc=doc,
            key='data',
            data={'a': 1, 'b': 2, 'foo': {'c': 3, 'd': 4, 'bar': {'e': 5, 'f': 6}}},
        )
        self.assert_content(
            doc.as_string(),
            inspect.cleandoc(
                '''
                [data]
                a = 1
                b = 2

                [data.foo]
                c = 3
                d = 4

                [data.foo.bar]
                e = 5
                f = 6
                '''
            ),
        )
        # Update existing data:
        add_or_update_nested_dict(
            doc=doc,
            key='data',
            data={'a': 1, 'foo': {'c': 333, 'bar': {'e': 666}}},
        )
        self.assert_content(
            doc.as_string(),
            inspect.cleandoc(
                '''
                [data]
                a = 1

                [data.foo]
                c = 333

                [data.foo.bar]
                e = 666
                '''
            ),
        )

        doc = tomlkit.document()
        data = {'foo': [1, 2, 3, {'bar': [4, 5, 6, {'baz': 7}]}]}
        add_or_update_nested_dict(doc=doc, key='data', data=data)
        result = doc.as_string()
        self.assert_content(
            result,
            inspect.cleandoc(
                '''
                [data]
                foo = [1, 2, 3, {bar = [4, 5, 6, {baz = 7}]}]
                '''
            ),
        )
        doc = tomlkit.parse(result)
        self.assertEqual(dict(doc)['data'], data)

    def test_basic(self):
        with TemporaryDirectory(prefix='test_basic') as temp_path:
            toml = PyProjectToml(project_path=temp_path)

            self.assertEqual(toml.path, temp_path / 'pyproject.toml')
            self.assertFalse(toml.path.exists())

            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    '''
                ),
            )
            self.assertEqual(
                toml.get_mp_meta(),
                ManageProjectsMeta(
                    initial_revision=None,
                    applied_migrations=[],
                    cookiecutter_template=None,
                    cookiecutter_directory=None,
                    cookiecutter_context=None,
                    initial_date=None,
                ),
            )

            toml.init(
                revision='abc0001',
                dt=parse_dt('2000-01-01T00:00:00+0000'),
                template='https://github.com/jedie/mp_test_template1/',
                directory='test_template1',
            )
            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "abc0001"
                    initial_date = 2000-01-01T00:00:00Z
                    cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
                    cookiecutter_directory = "test_template1"
                    '''
                ),
            )

            toml.create_or_update_cookiecutter_context(
                context={
                    'cookiecutter': {
                        'foo': 'bar',
                        'x': 1,
                        '_template': '/foo/bar',
                        '_output_dir': '/tmp/test/',
                    }
                }
            )
            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "abc0001"
                    initial_date = 2000-01-01T00:00:00Z
                    cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
                    cookiecutter_directory = "test_template1"

                    [manageprojects.cookiecutter_context.cookiecutter]
                    foo = "bar"
                    x = 1
                    _template = "/foo/bar"
                    _output_dir = "/tmp/test/"
                    '''
                ),
            )

            # Reopen and get the information back:
            toml = PyProjectToml(project_path=temp_path)
            self.assertEqual(
                toml.get_mp_meta(),
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+0000'),
                    applied_migrations=[],
                    cookiecutter_template='https://github.com/jedie/mp_test_template1/',
                    cookiecutter_directory='test_template1',
                    cookiecutter_context={
                        'cookiecutter': {
                            'foo': 'bar',
                            'x': 1,
                            '_template': '/foo/bar',
                            '_output_dir': '/tmp/test/',
                        }
                    },
                ),
            )

            # add migration info
            toml.add_applied_migrations(git_hash='abc0002', dt=parse_dt('2000-02-02T00:00:00+0000'))
            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "abc0001"
                    initial_date = 2000-01-01T00:00:00Z
                    cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
                    cookiecutter_directory = "test_template1"
                    applied_migrations = [
                        "abc0002", # 2000-02-02T00:00:00+00:00
                    ]

                    [manageprojects.cookiecutter_context.cookiecutter]
                    foo = "bar"
                    x = 1
                    _template = "/foo/bar"
                    _output_dir = "/tmp/test/"
                    '''
                ),
            )

            toml.add_applied_migrations(git_hash='abc0003', dt=parse_dt('2000-03-03T00:00:00+0000'))
            toml.create_or_update_cookiecutter_context(
                context={
                    'cookiecutter': {
                        'foo': 'overwritten',
                        'x': 2,
                        'new': 'value',
                        '_template': '/foo/bar',
                        '_output_dir': '/tmp/test/',
                    }
                }
            )
            toml.save()
            self.assert_file_content(
                toml.path,
                inspect.cleandoc(
                    '''
                    # Created by manageprojects

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "abc0001"
                    initial_date = 2000-01-01T00:00:00Z
                    cookiecutter_template = "https://github.com/jedie/mp_test_template1/"
                    cookiecutter_directory = "test_template1"
                    applied_migrations = [
                        "abc0002", # 2000-02-02T00:00:00+00:00
                        "abc0003", # 2000-03-03T00:00:00+00:00
                    ]

                    [manageprojects.cookiecutter_context.cookiecutter]
                    foo = "overwritten"
                    x = 2
                    new = "value"
                    _template = "/foo/bar"
                    _output_dir = "/tmp/test/"
                    '''
                ),
            )
            self.assertEqual(
                toml.get_mp_meta(),
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+0000'),
                    applied_migrations=['abc0002', 'abc0003'],
                    cookiecutter_template='https://github.com/jedie/mp_test_template1/',
                    cookiecutter_directory='test_template1',
                    cookiecutter_context={
                        'cookiecutter': {
                            'foo': 'overwritten',
                            'x': 2,
                            'new': 'value',
                            '_template': '/foo/bar',
                            '_output_dir': '/tmp/test/',
                        }
                    },
                ),
            )

    def test_expand_existing_toml(self):
        with TemporaryDirectory(prefix='test_basic') as temp_path:
            file_path = temp_path / 'pyproject.toml'
            file_path.write_text(
                inspect.cleandoc(
                    '''
                    [project]
                    name = "manageprojects"
                    version = "0.0.2rc1"

                    [project.urls]
                    "Homepage" = "https://github.com/jedie/manageproject"
                    "Bug Tracker" = "https://github.com/jedie/manageproject/issues"
                    '''
                )
            )

            toml = PyProjectToml(project_path=temp_path)
            toml.init(
                revision='abc0001',
                dt=parse_dt('2000-01-01T00:00:00+0000'),
                template='/foo/bar/template',
                directory=None,
            )
            toml.save()

            self.assert_file_content(
                file_path,
                inspect.cleandoc(
                    '''
                    [project]
                    name = "manageprojects"
                    version = "0.0.2rc1"

                    [project.urls]
                    "Homepage" = "https://github.com/jedie/manageproject"
                    "Bug Tracker" = "https://github.com/jedie/manageproject/issues"

                    [manageprojects] # https://github.com/jedie/manageprojects
                    initial_revision = "abc0001"
                    initial_date = 2000-01-01T00:00:00Z
                    cookiecutter_template = "/foo/bar/template"
                    '''
                ),
            )
            self.assertEqual(
                toml.get_mp_meta(),
                ManageProjectsMeta(
                    initial_revision='abc0001',
                    initial_date=parse_dt('2000-01-01T00:00:00+0000'),
                    applied_migrations=[],
                    cookiecutter_template='/foo/bar/template',
                    cookiecutter_directory=None,
                    cookiecutter_context=None,
                ),
            )
