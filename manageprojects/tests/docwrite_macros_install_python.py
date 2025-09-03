import argparse
from argparse import ArgumentParser
import datetime
from pathlib import Path
import tempfile
from unittest.mock import patch

from bx_py_utils.doc_write.data_structures import MacroContext
from bx_py_utils.path import assert_is_file
from gnupg import GPG, ImportResult

from manageprojects import install_python
from manageprojects.install_python import (
    DEFAULT_INSTALL_PREFIX,
    GPG_KEY_IDS,
    GPG_KEY_SERVER,
    PY_FTP_INDEX_URL,
    TEMP_PREFIX,
)


EXAMPLE_SCRIPT_PATH = Path(install_python.__file__).parent / 'install_python_example.sh'


class HelpFormatterMock(argparse.ArgumentDefaultsHelpFormatter):

    def __init__(self, *args, **kwargs):
        kwargs['width'] = 120
        kwargs['prog'] = Path(install_python.__file__).name  # Force: 'install_python.py'
        super().__init__(*args, **kwargs)


def help(macro_context: MacroContext):
    with patch.object(argparse, 'ArgumentDefaultsHelpFormatter', HelpFormatterMock):
        parser: ArgumentParser = install_python.get_parser()
        yield parser.format_help()


def supported_python_versions(macro_context: MacroContext):
    yield ''
    yield '| Version | GPG Key ID |'
    yield '|:-------:|------------|'
    for version, gpg_key in sorted(GPG_KEY_IDS.items()):
        yield f'| **{version}** | `{gpg_key}` |'

    yield '\n## GPG Key Information:\n'

    def timestamp2isoformat(timestamp: str) -> str:
        date = datetime.date.fromtimestamp(int(timestamp))
        return date.isoformat()

    with tempfile.TemporaryDirectory() as temp_dir:
        gpg_key_ids = set(GPG_KEY_IDS.values())
        gpg = GPG(env={'GNUPGHOME': temp_dir})
        result: ImportResult = gpg.recv_keys(GPG_KEY_SERVER, *gpg_key_ids)
        for key_details in sorted(gpg.list_keys(keys=result.fingerprints), key=lambda x: x['date'], reverse=True):
            creation_date = timestamp2isoformat(key_details['date'])
            if expires := key_details['expires']:
                expiration_date = timestamp2isoformat(expires)
            else:
                expiration_date = None
            yield f'* Key ID: `{key_details["keyid"]}`'
            yield '* User IDs:'
            for uid in key_details['uids']:
                yield f'  * {uid}'
            yield f'* Fingerprint: `{key_details["fingerprint"]}`'
            yield f'* Creation: {creation_date}'
            yield f'* Expiration: {expiration_date or "-"}'
            yield '\n'


def ftp_url(macro_context: MacroContext):
    yield f' * {PY_FTP_INDEX_URL}'


def default_install_prefix(macro_context: MacroContext):
    yield f' * `{DEFAULT_INSTALL_PREFIX}`\n\n'


def temp_prefix(macro_context: MacroContext):
    yield f' * `{TEMP_PREFIX}`'


def example_shell_script(macro_context: MacroContext):
    assert_is_file(EXAMPLE_SCRIPT_PATH)

    yield '\n```shell'
    yield EXAMPLE_SCRIPT_PATH.read_text()
    yield '```'
