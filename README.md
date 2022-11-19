# manageprojects - Manage Python / Django projects

[![tests](https://github.com/jedie/manageprojects/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/manageprojects/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/manageprojects/branch/main/graph/badge.svg)](https://codecov.io/github/jedie/manageprojects)
[![manageprojects @ PyPi](https://img.shields.io/pypi/v/manageprojects?label=manageprojects%20%40%20PyPi)](https://pypi.org/project/manageprojects/)
[![Python Versions](https://img.shields.io/pypi/pyversions/manageprojects)](https://github.com/jedie/manageprojects/blob/main/pyproject.toml)
[![License GPL](https://img.shields.io/pypi/l/manageprojects)](https://github.com/jedie/manageprojects/blob/main/LICENSE)

Mix the idea of Ansible with CookieCutter Templates and Django Migrations to manage and update your Python Packages and Django Projects...


## start hacking

```bash
~$ git clone https://github.com/jedie/manageprojects.git
~$ cd manageprojects
~/manageprojects$ ./mp.py --help

+ /home/jens/repos/manageprojects/.venv/bin/manageprojects --help


 Usage: manageprojects [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                         │
│ --show-completion             Show completion for the current shell, to copy it or customize    │
│                               the installation.                                                 │
│ --help                        Show this message and exit.                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────╮
│ check-code-style                                                                                │
│ coverage          Run and show coverage.                                                        │
│ fix-code-style    Fix code style via darker                                                     │
│ install           Run pip-sync and install 'manageprojects' via pip as editable.                │
│ mypy              Run Mypy (configured in pyproject.toml)                                       │
│ publish           Build and upload this project to PyPi                                         │
│ start-project     Start a new "managed" project via a CookieCutter Template                     │
│ test              Run unittests                                                                 │
│ update            Update the development environment by calling: - pip-compile production.in    │
│                   develop.in -> develop.txt - pip-compile production.in -> production.txt -     │
│                   pip-sync develop.txt                                                          │
│ update-project    Update a existing project.                                                    │
│ version           Print version and exit                                                        │
│ wiggle            Run wiggle to merge *.rej in given directory.                                 │
│                   https://github.com/neilbrown/wiggle                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────╯
```


## Links

* https://github.com/jedie/cookiecutter_templates
* https://github.com/cookiecutter/cookiecutter
* Available Cookiecutters template on GitHub: https://github.com/search?q=cookiecutter&type=Repositories
* Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
