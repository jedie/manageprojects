from pathlib import Path

from manageprojects.cookiecutter_generator import (
    build_dst_path,
    generate_reverse_info,
    iter_context,
    replace_path,
)
from manageprojects.tests.base import BaseTestCase


class CookiecutterGeneratorTestCase(BaseTestCase):
    def test_iter_context(self):
        result = list(
            iter_context(
                context={
                    'cookiecutter': {
                        '_template': 'https://github.com/jedie/cookiecutter_templates/',
                        'package_name': 'PyInventory',
                        'package_url': 'https://github.com/jedie/PyInventory',
                        'issues_url': 'https://github.com/jedie/PyInventory/issues',
                    }
                }
            )
        )
        self.assertEqual(
            result,
            [
                ('cookiecutter.package_name', 'PyInventory'),
                ('cookiecutter.package_url', 'https://github.com/jedie/PyInventory'),
                ('cookiecutter.issues_url', 'https://github.com/jedie/PyInventory/issues'),
            ],
        )

    def test_generate_reverse_info(self):
        reverse_info = generate_reverse_info(
            cookiecutter_context={
                'cookiecutter': {
                    '_template': 'https://github.com/jedie/cookiecutter_templates/',
                    'package_name': 'PyInventory',
                    'package_url': 'https://github.com/jedie/PyInventory',
                    'issues_url': 'https://github.com/jedie/PyInventory/issues',
                }
            }
        )
        self.assertEqual(
            reverse_info,
            (
                ('https://github.com/jedie/PyInventory/issues', '{{ cookiecutter.issues_url }}'),
                ('https://github.com/jedie/PyInventory', '{{ cookiecutter.package_url }}'),
                ('PyInventory', '{{ cookiecutter.package_name }}'),
            ),
        )

    def test_replace_path(self):
        path = replace_path(
            path=Path('foo', 'bar', 'baz'),
            reverse_info=(
                ('foo', '{{ package_name }}'),
                ('bar', '{{ dir_name }}'),
                (['877e2ec', 'be3f649', 'c1a9d97'], '{{ cookiecutter.applied_migrations }}'),
            ),
        )
        self.assertEqual(path, Path('{{ package_name }}/{{ dir_name }}/baz'))

    def test_build_dst_path(self):
        path = build_dst_path(
            source_path=Path('/the/source/path/'),
            item=Path('/the/source/path/foo/bar/test.py'),
            destination=Path('/the/destination'),
            reverse_info=(
                ('foo', '{{ package_name }}'),
                ('bar', '{{ dir_name }}'),
            ),
        )
        self.assertEqual(
            path,
            Path('/the/destination/{{ package_name }}/{{ dir_name }}/test.py'),
        )
