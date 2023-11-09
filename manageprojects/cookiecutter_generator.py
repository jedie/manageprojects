import shutil
from pathlib import Path

from bx_py_utils.path import assert_is_dir
from cli_base.cli_tools.git import Git
from rich import print  # noqa
from rich.pretty import pprint


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


def replace_str(content: str, reverse_info: tuple, verbosity: int = 0) -> str:
    origin_content = content
    for src_str, dst_str in reverse_info:
        if isinstance(src_str, str) and isinstance(dst_str, str):
            content = content.replace(src_str, dst_str)
        elif verbosity > 2:
            if not isinstance(src_str, str):
                print(f'Ignore {src_str=} for {content=}')
            if not isinstance(dst_str, str):
                print(f'Ignore {dst_str=} for {content=}')

    if verbosity > 2 and content != origin_content:
        print(f'Convert: {origin_content} -> {content}')

    return content


def replace_path(*, path: Path, reverse_info: tuple, verbosity: int = 0) -> Path:
    new_parts = [replace_str(part, reverse_info=reverse_info, verbosity=verbosity) for part in path.parts]
    return Path(*new_parts)


def build_dst_path(
    *,
    source_path: Path,
    item: Path,
    destination: Path,
    reverse_info: tuple,
    verbosity: int = 0,
):
    rel_path = item.relative_to(source_path)
    if verbosity > 1:
        print(f'Store: {rel_path}', end=' ')
    new_path = replace_path(path=rel_path, reverse_info=reverse_info, verbosity=verbosity)
    if verbosity > 1:
        print(f'-> {new_path}')
    dst_path = destination / new_path
    return dst_path


def copy_replaced(src_path, dst_path, reverse_info: tuple, verbosity: int = 0):
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
        content = replace_str(content, reverse_info=reverse_info, verbosity=verbosity)
        dst_path.write_text(content, encoding='UTF-8')


def create_cookiecutter_template(
    *,
    source_path: Path,
    destination: Path,
    cookiecutter_context: dict,
    overwrite: bool = False,
    verbosity: int = 0,
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
        if verbosity > 1:
            print(f'Convert: {item}')
        dst_path = build_dst_path(
            source_path=source_path,
            item=item,
            destination=destination,
            reverse_info=reverse_info,
            verbosity=verbosity,
        )
        if item.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            print(item.relative_to(source_path), '->', dst_path)
            copy_replaced(src_path=item, dst_path=dst_path, reverse_info=reverse_info, verbosity=verbosity)
        else:
            print(f'Ignore: {item}')
