# manageprojects - Manage Python / Django projects

[![tests](https://github.com/jedie/manageprojects/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/manageprojects/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/manageprojects/branch/main/graph/badge.svg)](https://app.codecov.io/github/jedie/manageprojects)
[![manageprojects @ PyPi](https://img.shields.io/pypi/v/manageprojects?label=manageprojects%20%40%20PyPi)](https://pypi.org/project/manageprojects/)
[![Python Versions](https://img.shields.io/pypi/pyversions/manageprojects)](https://github.com/jedie/manageprojects/blob/main/pyproject.toml)
[![License GPL-3.0-or-later](https://img.shields.io/pypi/l/manageprojects)](https://github.com/jedie/manageprojects/blob/main/LICENSE)

Mix the idea of Ansible with CookieCutter Templates and Django Migrations to manage and update your Python Packages and Django Projects...

The main idea it to transfer changes of a CookieCutter template back to the created project.
Manageprojects used git to create a patch of the template changes and applies it to the created project.

Besides this, `manageprojects` also includes other generic helper for Python packages:

 * `publish_package()` - Build and upload a new release to PyPi, but with many pre-checks.
 * `format-file` - Format/Check a Python source file with Darker & Co., useful as IDE action.
 * `install_python.py` - [One file and no dependencies to install Python, if needed, from official Python FTP server, verified.](https://github.com/jedie/manageprojects/blob/main/docs/install_python.md)
 * `setup_python.py` - [One file and no dependencies to download and setup redistributable Python, if needed.](https://github.com/jedie/manageprojects/blob/main/docs/setup_python.md)

Read below the `Helper` section.

Documentation: [docs/](https://github.com/jedie/manageprojects/blob/main/docs/) (WIP)

## install

Currently just clone the project and just start the cli (that will create a virtualenv and installs every dependencies)

e.g.:
```bash
~$ git clone https://github.com/jedie/manageprojects.git
~$ cd manageprojects
~/manageprojects$ ./cli.py --help
```

The output of `./cli.py --help` looks like:

[comment]: <> (✂✂✂ auto generated main help start ✂✂✂)
```
Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ clone-project          Clone existing project by replay the cookiecutter template in a new       │
│                        directory.                                                                │
│ format-file            Format and check the given python source code file with                   │
│                        darker/autoflake/isort/pyupgrade/autopep8/mypy etc.                       │
│ reverse                Create a cookiecutter template from a managed project.                    │
│ start-project          Start a new "managed" project via a CookieCutter Template. Note: The      │
│                        CookieCutter Template *must* be use git!                                  │
│ update-project         Update a existing project.                                                │
│ update-readme-history  Update project history base on git commits/tags in README.md              │
│ version                Print version and exit                                                    │
│ wiggle                 Run wiggle to merge *.rej in given directory.                             │
│                        https://github.com/neilbrown/wiggle                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated main help end ✂✂✂)

### most important commands

#### start-project

Help from `./cli.py start-project --help` Looks like:

[comment]: <> (✂✂✂ auto generated start-project help start ✂✂✂)
```
Usage: ./cli.py start-project [OPTIONS] TEMPLATE OUTPUT_DIR

 Start a new "managed" project via a CookieCutter Template. Note: The CookieCutter Template *must*
 be use git!
 e.g.:
 ./cli.py start-project https://github.com/jedie/cookiecutter_templates/ --directory
 piptools-python ~/foobar/

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --directory             TEXT  Cookiecutter Option: Directory within repo that holds              │
│                               cookiecutter.json file for advanced repositories with multi        │
│                               templates in it                                                    │
│ --checkout              TEXT  Cookiecutter Option: branch, tag or commit to checkout after git   │
│                               clone                                                              │
│ --input/--no-input            Cookiecutter Option: Do not prompt for parameters and only use     │
│                               cookiecutter.json file content                                     │
│                               [default: input]                                                   │
│ --replay/--no-replay          Cookiecutter Option: Do not prompt for parameters and only use     │
│                               information entered previously                                     │
│                               [default: no-replay]                                               │
│ --password              TEXT  Cookiecutter Option: Password to use when extracting the           │
│                               repository                                                         │
│ --config-file           FILE  Cookiecutter Option: Optional path to "cookiecutter_config.yaml"   │
│ --help                        Show this message and exit.                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated start-project help end ✂✂✂)


#### update-project

Help from `./cli.py update-project --help` Looks like:

[comment]: <> (✂✂✂ auto generated update-project help start ✂✂✂)
```
Usage: ./cli.py update-project [OPTIONS] PROJECT_PATH

 Update a existing project.
 e.g. update by overwrite (and merge changes manually via git):
 ./cli.py update-project ~/foo/bar/

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --overwrite/--no-overwrite          Overwrite all Cookiecutter template files to the last        │
│                                     template state and do not apply the changes via git patches. │
│                                     The developer is supposed to apply the differences manually  │
│                                     via git. Will be aborted if the project git repro is not in  │
│                                     a clean state.                                               │
│                                     [default: overwrite]                                         │
│ --password                    TEXT  Cookiecutter Option: Password to use when extracting the     │
│                                     repository                                                   │
│ --config-file                 FILE  Cookiecutter Option: Optional path to                        │
│                                     "cookiecutter_config.yaml"                                   │
│ --input/--no-input                  Cookiecutter Option: Do not prompt for parameters and only   │
│                                     use cookiecutter.json file content                           │
│                                     [default: no-input]                                          │
│ --cleanup/--no-cleanup              Cleanup created temporary files [default: cleanup]           │
│ --help                              Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated update-project help end ✂✂✂)



## workflow

### 1. Create a new project

Use `start-project` command and a github url as Cookiecutter template, e.g.:

```bash
~/manageprojects$ ./cli.py start-project https://github.com/jedie/cookiecutter_templates/ --directory piptools-python ~/my_new_project/
~/manageprojects$ cd ~/my_new_project/your_cool_package/
~/my_new_project/your_cool_package/$ git init
~/my_new_project/your_cool_package/$ git add .
~/my_new_project/your_cool_package/$ git commit --message "my cool new project"
```

Note: https://github.com/jedie/cookiecutter_templates is a multi template repository, the `piptools-python` template is here: https://github.com/jedie/cookiecutter_templates/tree/main/piptools-python

After running the `start-project` command, look into the created files.
Manage projects stores all needed meta information about the used Cookiecutter template into `pyproject.toml`, e.g.:
```bash
~/manageprojects$ cat ~/my_new_project/your_cool_package/pyproject.toml
...
[manageprojects] # https://github.com/jedie/manageprojects
initial_revision = "6e4c875"
initial_date = 2022-11-10T12:37:20+01:00
cookiecutter_template = "https://github.com/jedie/cookiecutter_templates/"
cookiecutter_directory = "piptools-python"

[manageprojects.cookiecutter_context.cookiecutter]
...
```

### 2. Update existing project

If the source Cookiecutter changed, then you can apply these changes to your created project, e.g.:

```bash
~/manageprojects$ ./cli.py update-project ~/my_new_project/your_cool_package/
```

After this, manageproject will update the own meta information in `pyproject.toml` by add `applied_migrations` with the information about the current Cookiecutter version, e.g.:
```bash
~/manageprojects$ cat ~/my_new_project/your_cool_package/pyproject.toml
...
[manageprojects] # https://github.com/jedie/manageprojects
initial_revision = "6e4c875"
initial_date = 2022-11-10T12:37:20+01:00
cookiecutter_template = "https://github.com/jedie/cookiecutter_templates/"
cookiecutter_directory = "piptools-python"
applied_migrations = [
    "dd69dcf", # 2022-11-22T19:48:28+01:00
]
...
```

## How?

Everything is based on git ;)

* manageprojects knows the git hash of the used Cookiecutter Template at creation time and the current git hash.
* It builds a git patch between these two commits.
* This patch will be applied to the created project sources.

So theoretically the changes in the template are applied to the project.

However, this does not work in every case, because git can't match the changes.

See below:

## drawbacks

One problem is that git can't apply all changes.

But `git apply` is used with `--reject`.
It applies the parts of the patch that are applicable,
and leave the rejected hunks in corresponding `*.rej` files.

There is a cool tool, called `wiggle`: https://github.com/neilbrown/wiggle

It tries to apply rejected patches by perform word-wise diffs.

Just run `wiggle` via manageproject CLI, e.g.:

```bash
~/manageprojects$ ./cli.py wiggle ~/my_new_project/your_cool_package/
```


#### Update by overwrite

A alternative way to update a project:

1. Just overwrite all files with the current Cookiecutter template output
2. Merge changes manually via `git`

So you doesn't have trouble with not applicable git patches ;)

Just add `--overwrite`, e.g.:
```bash
~/manageprojects$ ./cli.py update-project --overwrite ~/my_new_project/your_cool_package/
```


## Helper

Below are some generic tools helpful for Python packages.


### install_python.py

A script to download, build and install a Python interpreter, but only if the system Python is not the required major version.
It's a standalone script with no dependencies. Works with Python 3.9+.

More information: [docs/install_python.md](https://github.com/jedie/manageprojects/blob/main/docs/install_python.md)


### "reverse" - Reverse a project into a Cookiecutter template

A existing managed project can be converted back to a Cookiecutter template, e.g.:
```bash
~/manageprojects$ ./cli.py reverse ~/my_new_project/ ~/cookiecutter_template/
```


### "format-file" - Format and check the given python source code file

You can use `format-file` as "Action on save" or manual action in your IDE to fix code style ;)

[comment]: <> (✂✂✂ auto generated format-file help start ✂✂✂)
```
Usage: ./cli.py format-file [OPTIONS] FILE_PATH

 Format and check the given python source code file with
 darker/autoflake/isort/pyupgrade/autopep8/mypy etc.
 The optional fallback values will be only used, if we can't get them from the project meta files
 like ".editorconfig" and "pyproject.toml"

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --py-version                     TEXT     Fallback Python version for darker/pyupgrade, if       │
│                                           version is not defined in pyproject.toml               │
│                                           [default: 3.10]                                        │
│ --max-line-length            -l  INTEGER  Fallback max. line length for darker/isort etc., if    │
│                                           not defined in .editorconfig                           │
│                                           [default: 119]                                         │
│ --darker-prefixes                TEXT     Apply prefixes via autopep8 before calling darker.     │
│                                           [default: E301,E302,E303,E305,W391]                    │
│ --remove-all-unused-imports               Remove all unused imports (not just those from the     │
│                                           standard library) via autoflake                        │
│                                           [default: True]                                        │
│ --help                                    Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated format-file help end ✂✂✂)


### publish

The `manageprojects.utilities.publish.publish_package()` is designed for external packages, too.

Build and upload (with twine) a project to PyPi with many pre-checks:

 * Has correct version number?
 * Is on main branch and up-to-date with origin?
 * Check if current version already published
 * Build a git tag based on current package version
 * Adds change messages since last release to git tag message

Some checks result in a hard exit, but some can be manually confirmed from the user to continue publishing.

## development

For developing manageprojects, there is the `dev-cli.py`.

The output of `./dev-cli.py --help` looks like:

[comment]: <> (✂✂✂ auto generated dev help start ✂✂✂)
```
Usage: ./dev-cli.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────╮
│ build                       Build the manageproject (More a test of                              │
│                             manageprojects.utilities.publish.build)                              │
│ check-code-style            Check code style by calling darker + flake8                          │
│ coverage                    Run tests and show coverage report.                                  │
│ fix-code-style              Fix code style of all manageprojects source code files via darker    │
│ git-hooks                   Setup our "pre-commit" git hooks                                     │
│ install                     Install requirements and 'manageprojects' via pip as editable.       │
│ mypy                        Run Mypy (configured in pyproject.toml)                              │
│ nox                         Run nox                                                              │
│ pip-audit                   Run pip-audit check against current requirements files               │
│ publish                     Build and upload this project to PyPi                                │
│ run-git-hooks               Run the installed "pre-commit" git hooks                             │
│ test                        Run unittests                                                        │
│ update                      Update "requirements*.txt" dependencies files                        │
│ update-readme-history       Update project history base on git commits/tags in README.md         │
│ update-test-snapshot-files  Update all test snapshot files (by remove and recreate all snapshot  │
│                             files)                                                               │
│ version                     Print version and exit                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
[comment]: <> (✂✂✂ auto generated dev help end ✂✂✂)

## development git hooks

To install the git hooks, run:

```bash
~/manageprojects$ ./dev-cli.py git-hooks
```


## History

See also git tags: https://github.com/jedie/manageprojects/tags

[comment]: <> (✂✂✂ auto generated history start ✂✂✂)

* [v0.21.2](https://github.com/jedie/manageprojects/compare/v0.21.1...v0.21.2)
  * 2025-03-11 - Fix nox CLI call
  * 2025-03-11 - Update requirements and replace tox with nox
* [v0.21.1](https://github.com/jedie/manageprojects/compare/v0.21.0...v0.21.1)
  * 2025-01-31 - Use cli_tools.path_utils.which
* [v0.21.0](https://github.com/jedie/manageprojects/compare/v0.20.0...v0.21.0)
  * 2025-01-17 - Prefere to build with "uv build"
  * 2025-01-17 - Update requirements
* [v0.20.0](https://github.com/jedie/manageprojects/compare/v0.19.2...v0.20.0)
  * 2024-11-11 - Bugfix publish: Add "build" dep.
  * 2024-11-11 - Bugfix publish command: Add missing "setuptools" dep.
  * 2024-11-11 - Switch to uv
  * 2024-09-25 - Add: test_pre_commit_hooks()
  * 2024-09-25 - Move git pre-commit hook from dev-cli.py to update command

<details><summary>Expand older history entries ...</summary>

* [v0.19.2](https://github.com/jedie/manageprojects/compare/v0.19.1...v0.19.2)
  * 2024-09-24 - Add piwheels hashes, too.
  * 2024-09-24 - Apply update from cookiecutter templates
  * 2024-09-24 - Update requirements
* [v0.19.1](https://github.com/jedie/manageprojects/compare/v0.19.0...v0.19.1)
  * 2024-09-15 - Bugfix and enhance "setup_python.py"
* [v0.19.0](https://github.com/jedie/manageprojects/compare/v0.18.0...v0.19.0)
  * 2024-09-15 - NEW: setup_python.py
  * 2024-09-15 - Update requirements
* [v0.18.0](https://github.com/jedie/manageprojects/compare/v0.17.1...v0.18.0)
  * 2024-08-29 - Fix wrong "module" in publish call :(
  * 2024-08-29 - Fix wrong "distribution_name" in publish command
  * 2024-08-29 - Update typeannotations
  * 2024-08-29 - Fix wrong typeannotation
  * 2024-08-29 - Add IncludeInstallPythonBaseTestCase to auto update 'install_python.py'
  * 2024-08-29 - Add: .pre-commit-hooks.yaml
  * 2024-08-29 - NEW: install_python.py
  * 2024-08-29 - Fix CI + tox
  * 2024-08-29 - Update tox envlist to github action matrix
  * 2024-08-29 - Bugfix update pyproject_toml.py via cookiecutter template
  * 2024-08-29 - Update requirements + apply template updates
  * 2024-03-08 - Run "refurb", too.
  * 2024-01-16 - add and use typeguard in tests
  * 2024-07-09 - Split CLI
  * 2024-02-22 - Update requirements
  * 2023-12-30 - Fix typos
* [v0.17.1](https://github.com/jedie/manageprojects/compare/v0.17.0...v0.17.1)
  * 2023-12-29 - Still support Python v3.9
* [v0.17.0](https://github.com/jedie/manageprojects/compare/v0.16.2...v0.17.0)
  * 2023-12-21 - Bugfix: Don't loose the "[manageprojects]" content on overwrite-update
  * 2023-12-21 - typing: Optional -> None
  * 2023-12-21 - Unify BASE_PATH / PACKAGE_ROOT etc.
  * 2023-12-21 - Apply manageprojects updates: Skip Python 3.9 support
  * 2023-12-21 - Update requirements
* [v0.16.2](https://github.com/jedie/manageprojects/compare/v0.16.1...v0.16.2)
  * 2023-12-16 - Update pre-commit-config
  * 2023-12-16 - Skip test_readme_history() on CI
  * 2023-12-16 - Add git hook "update-readme-history"
  * 2023-12-16 - Apply cookiecutter updates
  * 2023-12-16 - Update requirements
* [v0.16.1](https://github.com/jedie/manageprojects/compare/v0.16.0...v0.16.1)
  * 2023-12-05 - Fix "format file" and very verbose error output
* [v0.16.0](https://github.com/jedie/manageprojects/compare/v0.15.4...v0.16.0)
  * 2023-12-02 - Use code style tooling from cli-base-utilities
  * 2023-12-01 - Apply https://github.com/jedie/cookiecutter_templates updates
  * 2023-12-01 - Use: cli_base.cli_tools.test_utils.logs.AssertLogs
* [v0.15.4](https://github.com/jedie/manageprojects/compare/v0.15.3...v0.15.4)
  * 2023-11-27 - Use "flake8-bugbear", too.
* [v0.15.3](https://github.com/jedie/manageprojects/compare/v0.15.2...v0.15.3)
  * 2023-11-09 - Bugfix "reverse" if context contains a list
  * 2023-11-07 - Update requirements
* [v0.15.2](https://github.com/jedie/manageprojects/compare/v0.15.1...v0.15.2)
  * 2023-11-01 - Update requirements
* [v0.15.1](https://github.com/jedie/manageprojects/compare/v0.15.0...v0.15.1)
  * 2023-10-08 - Update text matrix with Python v3.12
  * 2023-10-08 - fix github CI
  * 2023-10-08 - Update for CookieCutter v2.4.0 changes
  * 2023-10-08 - Autogenerate history via https://github.com/jedie/cli-base-utilities
  * 2023-09-24 - apply migrations
  * 2023-09-24 - Update requirements
* [v0.15.0](https://github.com/jedie/manageprojects/compare/v0.14.1...v0.15.0)
  * 2023-08-17 - Deprecate Git
  * 2023-08-17 - Deprecate print_version() (moved to cli_base)
* [v0.14.1](https://github.com/jedie/manageprojects/compare/v0.14.0...v0.14.1)
  * 2023-08-17 - apply project template updates and update requirements
  * 2023-08-15 - Update requirements
* [v0.14.0](https://github.com/jedie/manageprojects/compare/v0.13.0...v0.14.0)
  * 2023-08-09 - Use https://github.com/jedie/cli-base-utilities
* [v0.13.0](https://github.com/jedie/manageprojects/compare/v0.12.1...v0.13.0)
  * 2023-08-05 - publish: Support "dynamic metadata" from setuptools for the version
  * 2023-08-05 - Split CLI
* [v0.12.1](https://github.com/jedie/manageprojects/compare/v0.12.0...v0.12.1)
  * 2023-06-11 - Ehance git.push() by adding `get_output` to method
* [v0.12.0](https://github.com/jedie/manageprojects/compare/v0.11.0...v0.12.0)
  * 2023-06-11 - New: git.get_remote_url() and git.get_github_username()
* [v0.11.0](https://github.com/jedie/manageprojects/compare/v0.10.0...v0.11.0)
  * 2023-06-11 - Update requirements and relase as v0.11.0
  * 2023-06-11 - Enhance Git()
  * 2023-05-12 - Use "--remove-all-unused-imports" as default for autoflake
* [v0.10.0](https://github.com/jedie/manageprojects/compare/v0.9.10...v0.10.0)
  * 2023-05-11 - Enhance "format-file" and add "autoflake" to remove unused imports
  * 2023-04-10 - Update requirements
  * 2023-04-10 - apply manageprojects updates
  * 2023-04-08 - Apply project updates
* [v0.9.10](https://github.com/jedie/manageprojects/compare/v0.9.9...v0.9.10)
  * 2023-04-08 - Add helper to find and get the "pyproject.toml" file
* [v0.9.9](https://github.com/jedie/manageprojects/compare/v0.9.8...v0.9.9)
  * 2023-04-04 - Set --overwrite as default in update-project command
  * 2023-04-04 - Cleanup requirements
  * 2023-04-04 - project updates
* [v0.9.8](https://github.com/jedie/manageprojects/compare/v0.9.7...v0.9.8)
  * 2023-04-04 - Add `--overwrite` option to `reverse` command
* [v0.9.7](https://github.com/jedie/manageprojects/compare/v0.9.6...v0.9.7)
  * 2023-04-03 - Bugfix reverse command: Optimize replacements
  * 2023-03-17 - apply code migrations
* [v0.9.6](https://github.com/jedie/manageprojects/compare/v0.9.4...v0.9.6)
  * 2023-03-12 - Speedup: Install as editable with '--no-deps'
  * 2023-03-12 - Fix #68 Handle if there are no git tags while publishing
  * 2023-03-11 - Bugfix reverse command and binary files
* [v0.9.4](https://github.com/jedie/manageprojects/compare/v0.9.3...v0.9.4)
  * 2023-03-09 - Support "poerty" in publish_package(), too.
* [v0.9.3](https://github.com/jedie/manageprojects/compare/v0.9.2...v0.9.3)
  * 2023-03-07 - Fix publish
  * 2023-03-07 - Update project
  * 2023-03-06 - coverage xml report + CLI
  * 2023-03-06 - Update README.md
  * 2023-03-06 - Fix CI / coverage run
  * 2023-03-06 - Remove "python_version < 3.11" for "tomli"
  * 2023-03-06 - merge cookie cutter template updates
* [v0.9.2](https://github.com/jedie/manageprojects/compare/v0.9.1...v0.9.2)
  * 2023-02-26 - Make the Result available on an error
  * 2023-02-26 - update requirements
  * 2023-02-26 - invoke_click(): Raise exception if exists
  * 2023-02-23 - Add: "E301 - expected 1 blank line" to "format-file"
* [v0.9.1](https://github.com/jedie/manageprojects/compare/v0.9.0...v0.9.1)
  * 2023-02-22 - Bugfix publish a poetry package and get the version string from pyproject.toml
* [v0.9.0](https://github.com/jedie/manageprojects/compare/v0.8.3...v0.9.0)
  * 2023-02-21 - README
  * 2023-02-21 - Refactor publish command and make is useable for external packages, too.
  * 2023-02-21 - Enhance verbose_check_output: Display output on errors and exit
  * 2023-02-20 - Enhance SubprocessCallMock: Mock subprocess.run(), too.
* [v0.8.3](https://github.com/jedie/manageprojects/compare/v0.8.2...v0.8.3)
  * 2023-02-20 - Bugfix packaging: remove "tox" from normal, non-dev dependencies
* [v0.8.2](https://github.com/jedie/manageprojects/compare/v0.8.0...v0.8.2)
  * 2023-02-20 - Path(sys.executable).parent -> PY_BIN_PATH
  * 2023-02-20 - Add "E305" to darker prefixes
  * 2023-02-20 - Add tox config via manageprojects
  * 2023-02-19 - Add "W391 blank line at end of file" to darker pre fixes
  * 2023-02-19 - Add check_editor_config()
  * 2023-02-19 - CLI: Add "version" back as pseudo command.
  * 2023-02-19 - Better subprocess_utils API
* [v0.8.0](https://github.com/jedie/manageprojects/compare/v0.7.3...v0.8.0)
  * 2023-02-19 - Split "test_cli" and add "format-file" into README
  * 2023-02-18 - Add reuseable helper: print_version()
  * 2023-02-18 - NEW: "format-file"
  * 2023-02-18 - add Safety check
  * 2023-02-18 - apply manageprojects
* [v0.7.3](https://github.com/jedie/manageprojects/compare/v0.7.1...v0.7.3)
  * 2023-01-25 - Bugfix "--overwrite" if there are new directories in template
  * 2023-01-25 - Bugfix "overwrite" if there are new files
* [v0.7.1](https://github.com/jedie/manageprojects/compare/v0.7.0...v0.7.1)
  * 2023-01-25 - Add cli help pages into README using helper in bx_py_utils
* [v0.7.0](https://github.com/jedie/manageprojects/compare/v0.6.0...v0.7.0)
  * 2023-01-15 - Fix #41 Add "--overwrite" to "update-project" command
* [v0.6.0](https://github.com/jedie/manageprojects/compare/v0.5.0...v0.6.0)
  * 2023-01-14 - bugfix publish command
  * 2023-01-14 - NEW: "update-test-snapshot-files" command
  * 2023-01-14 - Fix tests
  * 2023-01-13 - Replace typer with the origin click
  * 2023-01-12 - apply migration
  * 2023-01-12 - Enhance CLI argument documentation
  * 2023-01-11 - update requirements
  * 2023-01-09 - Better code style test + fix via unittests
  * 2023-01-09 - Use RedirectOut from bx_py_utils v73
  * 2023-01-09 - Bugfix "./cli.py install" and wrong path to req. file
  * 2023-01-09 - reverse command: Use "git ls-files" instead of pathspec
* [v0.5.0](https://github.com/jedie/manageprojects/compare/v0.4.0...v0.5.0)
  * 2023-01-08 - NEW: Reverse a project into a Cookiecutter template
* [v0.4.0](https://github.com/jedie/manageprojects/compare/v0.3.3...v0.4.0)
  * 2022-12-30 - Refactor "dependencies" definition
  * 2022-12-30 - Bugfix Git(): Pass environment, but set "en_US" als language
  * 2022-12-30 - update requirements
  * 2022-12-30 - include all packages
  * 2022-12-30 - Capture and check log output in tests
  * 2022-12-30 - cleanup editorconfig
  * 2022-12-30 - enhance test run
  * 2022-12-30 - Bugfix wrong "hint"
* [v0.3.3](https://github.com/jedie/manageprojects/compare/v0.3.2...v0.3.3)
  * 2022-12-21 - Update requirements
  * 2022-12-21 - Use new pip-compile resolver
  * 2022-12-21 - Bugfix if git output will be translated.
  * 2022-11-30 - Fix help by adding './cli.py' and add basic CLI tests
  * 2022-11-30 - Enhance "start-project" and "update-project" CLI help pages
  * 2022-11-30 - Update README.md
  * 2022-11-22 - update reqirements
  * 2022-11-20 - SELF MANAGE !!!
  * 2022-11-20 - fix typo
  * 2022-11-20 - rename: "./mp.py" -> "./cli.py"
* [v0.3.2](https://github.com/jedie/manageprojects/compare/16ee951...v0.3.2)
  * 2022-11-19 - git tag on publish
  * 2022-11-19 - udpate requirements
  * 2022-11-19 - init_git(): Add a "fake" origin and push the current branch to it
  * 2022-11-19 - Update README.md
  * 2022-11-15 - Bugfix packaging: Release as 0.3.1
  * 2022-11-15 - Move test utilities to normal package
  * 2022-11-15 - update requirements
  * 2022-11-15 - code cleanup
  * 2022-11-10 - remove own templates -> https://github.com/jedie/cookiecutter_templates
  * 2022-11-10 - Bugfix start project with own templates
  * 2022-11-10 - NEW: Clone a existing project by replay the cookiecutter template in a new directory.
  * 2022-11-10 - Display "git apply patch" output
  * 2022-11-10 - Bugfix reset "pyproject.toml" by overwriting with old content
  * 2022-11-09 - Use the origin unitest CLI
  * 2022-11-09 - Catch if git apply failes and add wiggle command to fix .rej files
  * 2022-11-09 - fix tests and set git user name/email if not exists
  * 2022-11-08 - Fix tests and more logging/output
  * 2022-11-07 - Bugfix patch paths
  * 2022-11-07 - Bugfix extra_context
  * 2022-11-07 - Generate better git diffs
  * 2022-11-07 - fix some optional typehints
  * 2022-11-07 - Better update project output
  * 2022-11-07 - add "cleanup" to CLI
  * 2022-11-07 - pass "no_input"
  * 2022-11-07 - change tomlkit.Container to a normal dict
  * 2022-11-07 - fix typo
  * 2022-11-07 - Better log config
  * 2022-11-06 - Add "update-project" to CLI
  * 2022-11-06 - +DocString for password
  * 2022-11-06 - fix double logging output
  * 2022-11-06 - Don't store "_output_dir" in pyproject.toml
  * 2022-11-04 - Fix version test if colors are enabled
  * 2022-11-04 - Bugfix exit tests on failour
  * 2022-11-03 - Simplify store the context to toml file
  * 2022-11-03 - refactor and fix tests
  * 2022-11-03 - Add --help in README
  * 2022-11-03 - Cookiecutter will only checkout a specific commit, if `template` is a repro url!
  * 2022-11-03 - Add "%(name)s" to log output
  * 2022-11-03 - Support optional `--test-path` for "./mp.py test"
  * 2022-11-03 - Rename "./mp.py unittest" to "./mp.py test"
  * 2022-11-01 - WIP: Refactor and add more tests
  * 2022-11-01 - Add cleanup argument in TemporaryDirectory
  * 2022-11-01 - move code
  * 2022-11-01 - Add and use log_func_call() helper
  * 2022-10-30 - Store/use Cookiecutter context untouched
  * 2022-10-30 - Add helper to convert nested dicts to toml
  * 2022-10-29 - WIP: enhance tests
  * 2022-10-29 - Fix typo and log more info
  * 2022-10-29 - Overwrite existing patch files
  * 2022-10-29 - fix some typehints
  * 2022-10-29 - WIP: update the existing project
  * 2022-10-28 - MOve som ecore parts + start "update project"
  * 2022-10-28 - Test start project with local template
  * 2022-10-27 - fix typing errors and activate "mypy" in tests
  * 2022-10-27 - Coverage: '--fail-under=50'
  * 2022-10-27 - test_git_apply_patch()
  * 2022-10-27 - Test git diff
  * 2022-10-27 - Add init_git() for tests
  * 2022-10-27 - Add test utils to generate git repositories "on-the-fly"
  * 2022-10-27 - Use assert_is_dir, assert_is_file from bx_py_utils
  * 2022-10-26 - Add 3.11 to CI
  * 2022-10-26 - fix ci coverage
  * 2022-10-26 - Store information into pyproject.toml
  * 2022-10-26 - setup coverage
  * 2022-10-26 - enhance log setup
  * 2022-10-25 - +requires-python = ">=3.9,<4.0.0"
  * 2022-10-25 - call "twine check" before upload
  * 2022-10-25 - +## start hacking
  * 2022-10-25 - fix badges
  * 2022-10-25 - fix CI
  * 2022-10-25 - Add .flak8 because of https://github.com/PyCQA/flake8/issues/234
  * 2022-10-25 - use unitests, add cookiecuttter helper add/fix tests and code style
  * 2022-10-24 - change cli+tests
  * 2022-10-24 - fix mypy call
  * 2022-10-24 - WIP
  * 2022-10-23 - chnage minimal template a little bit
  * 2022-10-23 - add first cookiecutter template
  * 2022-10-23 - Allow manageprojects CLI to be executable through `python -m manageprojects`.
  * 2022-10-22 - github actions
  * 2022-10-22 - dev
  * 2022-10-22 - bootstarp
  * 2022-10-22 - add requirements
  * 2022-10-22 - init Makefile
  * 2022-10-22 - Initial commit

</details>


[comment]: <> (✂✂✂ auto generated history end ✂✂✂)

## Links

* Own Cookiecutter Templates: https://github.com/jedie/cookiecutter_templates
* https://github.com/cookiecutter/cookiecutter
* Available Cookiecutters template on GitHub: https://github.com/search?q=cookiecutter&type=Repositories
* Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
