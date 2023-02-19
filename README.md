# manageprojects - Manage Python / Django projects

[![tests](https://github.com/jedie/manageprojects/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/jedie/manageprojects/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/jedie/manageprojects/branch/main/graph/badge.svg)](https://codecov.io/github/jedie/manageprojects)
[![manageprojects @ PyPi](https://img.shields.io/pypi/v/manageprojects?label=manageprojects%20%40%20PyPi)](https://pypi.org/project/manageprojects/)
[![Python Versions](https://img.shields.io/pypi/pyversions/manageprojects)](https://github.com/jedie/manageprojects/blob/main/pyproject.toml)
[![License GPL](https://img.shields.io/pypi/l/manageprojects)](https://github.com/jedie/manageprojects/blob/main/LICENSE)

Mix the idea of Ansible with CookieCutter Templates and Django Migrations to manage and update your Python Packages and Django Projects...

The main idea it to transfer changes of a CookieCutter template back to the created project.
Manageproject used git to create a patch of the template changes and applies it to the created project.

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
│ check-code-style            Check code style by calling darker + flake8                          │
│ clone-project               Clone existing project by replay the cookiecutter template in a new  │
│                             directory.                                                           │
│ coverage                    Run and show coverage.                                               │
│ fix-code-style              Fix code style of all manageprojects source code files via darker    │
│ format-file                 Format and check the given python source code file with              │
│                             darker/isort/pyupgrade/autopep8/mypy etc. Useful as manual action    │
│                             executed via IDE shortcut to fix and check a Python file.            │
│ install                     Run pip-sync and install 'manageprojects' via pip as editable.       │
│ mypy                        Run Mypy (configured in pyproject.toml)                              │
│ publish                     Build and upload this project to PyPi                                │
│ reverse                     Create a cookiecutter template from a managed project.               │
│ safety                      Run safety check against current requirements files                  │
│ start-project               Start a new "managed" project via a CookieCutter Template. Note: The │
│                             CookieCutter Template *must* be use git!                             │
│ test                        Run unittests                                                        │
│ update                      Update "requirements*.txt" dependencies files                        │
│ update-project              Update a existing project.                                           │
│ update-test-snapshot-files  Update all test snapshot files (by remove and recreate all snapshot  │
│                             files)                                                               │
│ wiggle                      Run wiggle to merge *.rej in given directory.                        │
│                             https://github.com/neilbrown/wiggle                                  │
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
 ./cli.py update-project --overwrite ~/foo/bar/

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --overwrite/--no-overwrite          Overwrite all Cookiecutter template files to the last        │
│                                     template state and do not apply the changes via git patches. │
│                                     The developer is supposed to apply the differences manually  │
│                                     via git. Will be aborted if the project git repro is not in  │
│                                     a clean state.                                               │
│                                     [default: no-overwrite]                                      │
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

So you doesn't have trouble with not applyable git patches ;)

Just add `--overwrite`, e.g.:
```bash
~/manageprojects$ ./cli.py update-project --overwrite ~/my_new_project/your_cool_package/
```


## Helper: Reverse a project into a Cookiecutter template

A existing managed project can be converted back to a Cookiecutter template, e.g.:
```bash
~/manageprojects$ ./cli.py reverse ~/my_new_project/ ~/cookiecutter_template/
```


## Links

* Own Cookiecutter Templates: https://github.com/jedie/cookiecutter_templates
* https://github.com/cookiecutter/cookiecutter
* Available Cookiecutters template on GitHub: https://github.com/search?q=cookiecutter&type=Repositories
* Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
