import shutil
from pathlib import Path

from bx_py_utils.path import assert_is_dir
from rich import print  # noqa
from rich.pretty import pprint

from manageprojects.git import Git


def iter_context(*, context: dict, prefix='') -> tuple:
    for key, value in context.items():
        if key.startswith('_'):
            continue

        if isinstance(value, dict):
            yield from iter_context(context=value, prefix=f'{key}.')
        else:
            yield (f'{prefix}{key}', value)


def generate_reverse_info(*, cookiecutter_context: dict) -> tuple:
    reverse_info = [
        (value, '{{ %s }}' % key) for key, value in iter_context(context=cookiecutter_context)
    ]
    reverse_info.sort(key=lambda x: len(x[0]), reverse=True)
    return tuple(reverse_info)


def replace_path(*, path: Path, reverse_info: tuple) -> Path:
    new_parts = []
    for part in path.parts:
        for src_str, dst_str in reverse_info:
            part = part.replace(src_str, dst_str)
        new_parts.append(part)
    return Path(*new_parts)


def build_dst_path(*, source_path: Path, item: Path, destination: Path, reverse_info: tuple):
    rel_path = item.relative_to(source_path)
    new_path = replace_path(path=rel_path, reverse_info=reverse_info)
    dst_path = destination / new_path
    return dst_path


def copy_replaced(src_path, dst_path, reverse_info):
    dst_parent = dst_path.parent
    dst_parent.mkdir(parents=True, exist_ok=True)

    try:
        content = src_path.read_text(encoding='UTF-8')
    except UnicodeDecodeError as err:
        # XXX: Detect binary files in a other way
        print(f'[yellow]Warning: {err} for file {src_path}')
        print('copy as binary file')
        shutil.copy2(src_path, dst_path)
    else:
        for src_str, dst_str in reverse_info:
            content = content.replace(src_str, dst_str)

        dst_path.write_text(content, encoding='UTF-8')


def create_cookiecutter_template(
    *,
    source_path: Path,
    destination: Path,
    cookiecutter_context: dict,
    overwrite: bool = False,
):
    source_path = source_path.resolve()
    assert_is_dir(source_path)
    if not overwrite:
        assert not destination.exists(), f'Destination {destination} already exists!'

    reverse_info = generate_reverse_info(cookiecutter_context=cookiecutter_context)

    print('Use this reverse context:')
    pprint(reverse_info)

    git = Git(cwd=source_path, detect_root=True)
    file_paths = git.ls_files(verbose=True)

    for item in file_paths:
        dst_path = build_dst_path(
            source_path=source_path,
            item=item,
            destination=destination,
            reverse_info=reverse_info,
        )
        if item.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            print(item.relative_to(source_path), '->', dst_path)
            copy_replaced(src_path=item, dst_path=dst_path, reverse_info=reverse_info)
        else:
            print(f'Ignore: {item}')
