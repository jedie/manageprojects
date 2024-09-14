# Install Python Interpreter

`install_python.py` downloads, builds and installs a Python interpreter, but:
- **only** if the system Python is not the required major version
- **only** once (if the required major version is not already build and installed)

Origin of this script is:
* https://github.com/jedie/manageprojects/blob/main/manageprojects/install_python.py

Licensed under GPL-3.0-or-later (Feel free to copy and use it in your project)

Minimal needed Python version to run the script is: **v3.9**.

Download Python source code from official Python FTP server:
 * https://www.python.org/ftp/python/

Download only over verified HTTPS connection.

The Downloaded tar archive will be verified with the GPG signature, if `gpg` is available.

## CLI

The CLI interface looks like e.g.:
```shell
$ python3 install_python.py --help

usage: install_python.py [-h] [-v] [--skip-temp-deletion] [--skip-write-check] [{3.10,3.11,3.12,3.13}]

Install Python Interpreter

positional arguments:
  {3.10,3.11,3.12,3.13}
                        Specify the Python version (default: 3.11)

options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity level (can be used multiple times, e.g.: -vv) (default: 0)
  --skip-temp-deletion  Skip deletion of temporary files (default: False)
  --skip-write-check    Skip the test for write permission to /usr/local/bin (default: False)

```

## Include in own projects

There is a unittest base class to include `install_python.py` script in your project.
If will check if the file is up2date and if not, it will update it.

Just include `manageprojects` as a dev dependency in your project.
And add a test like this:

```python
class IncludeInstallPythonTestCase(IncludeInstallPythonBaseTestCase):

    # Set the path where the `install_python.py` should be copied to:
    DESTINATION_PATH = Path(your_package.__file__).parent) / 'install_python.py'

    # The test will pass, if the file is up2date, if it's update the script!
    def test_install_python_is_up2date(self):
        self.auto_update_install_python()
```

Feel free to do it in a completely different way, this is just a suggestion ;)

## Supported Python Versions

The following major Python versions are supported and verified with GPG keys:

| Version | GPG Key ID |
|:-------:|------------|
| **3.10** | `64E628F8D684696D` |
| **3.11** | `64E628F8D684696D` |
| **3.12** | `A821E680E5FA6305` |
| **3.13** | `A821E680E5FA6305` |

## GPG Key Information:

* Key ID: `64E628F8D684696D`
* User IDs:
  * Pablo Galindo Salgado <pablogsal@gmail.com>
* Fingerprint: `A035C8C19219BA821ECEA86B64E628F8D684696D`
* Creation: 2018-03-30
* Expiration: -


* Key ID: `A821E680E5FA6305`
* User IDs:
  * Thomas Wouters <thomas@xs4all.nl>
  * Thomas Wouters <thomas@python.org>
  * Thomas Wouters <twouters@google.com>
* Fingerprint: `7169605F62C751356D054A26A821E680E5FA6305`
* Creation: 2015-03-11
* Expiration: 2026-07-02


The GPG keys taken from the official Python download page: https://www.python.org/downloads/

## Workflow

The setup process is as follows:

## Workflow - 1. Check system Python

If the system Python is the same major version as the required Python, we skip the installation.

The script just returns the path to the system Python interpreter.

## Workflow - 2. Get latest Python release

We fetch the latest Python release from the Python FTP server, from:
 * https://www.python.org/ftp/python/

## Workflow - 3. Check local installed Python

We assume that the `make altinstall` will install local Python interpreter into:
 * `/usr/local`


See: https://docs.python.org/3/using/configure.html#cmdoption-prefix

The script checks if the latest release already build and installed.

If the local Python is up-to-date, the script exist and returns the path this local interpreter.

## Workflow - 4. Download Python sources

Before we start building Python, check if we have write permissions.
The check can be skipped via CLI argument.

The download will be done in a temporary directory. The directory will be deleted after the installation.
This can be skipped via CLI argument. The directory will be prefixed with:
 * `setup_python_`

## Workflow - 5. Verify download

The sha256 hash downloaded tar archive will logged.
If `gpg` is available, the signature will be verified.

We set the `GNUPGHOME` environment variable to a temporary directory.

## Workflow - 6. Build and install Python

If the verify passed, the script will start the build process.

The installation will be done with `make altinstall`.

## Workflow - 7. print the path

If no errors occurred, the path to the Python interpreter will be printed to `stdout`.
So it's usable in shell scripts, like:

```shell
#!/usr/bin/env sh

set -e

PY_312_BIN=$(python3 install_python.py -v 3.12)
echo "Python 3.12 used from: '${PY_312_BIN}'"

set -x

${PY_312_BIN} -VV

```