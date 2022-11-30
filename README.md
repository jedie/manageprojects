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


## Links

* Own Cookiecutter Templates: https://github.com/jedie/cookiecutter_templates
* https://github.com/cookiecutter/cookiecutter
* Available Cookiecutters template on GitHub: https://github.com/search?q=cookiecutter&type=Repositories
* Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
