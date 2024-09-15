# Boot Redistributable Python

This is a standalone script (one file and no dependencies) to download and setup
https://github.com/indygreg/python-build-standalone/ redistributable Python.
But only if it's needed!

Minimal version to used this script is Python v3.9.

The downloaded archive will be verified with the hash checksum.

The download will be only done, if the system Python is not the same major version as requested
and if the local Python is not up-to-date.

## CLI

The CLI interface looks like e.g.:

```shell
$ python3 setup_python.py --help

usage: setup_python.py [-h] [-v] [--skip-temp-deletion] [--force-update] [major_version]

Download and setup redistributable Python Interpreter from https://github.com/indygreg/python-build-standalone/ if
needed ;)

positional arguments:
  major_version         Specify the Python version like: 3.10, 3.11, 3.12, ... (default: 3.12)

options:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity level (can be used multiple times, e.g.: -vv) (default: 0)
  --skip-temp-deletion  Skip deletion of temporary files (default: False)
  --force-update        Update local Python interpreter, even if it is up-to-date (default: False)

```

## Include in own projects

There is a unittest base class to include `setup_python.py` script in your project.
If will check if the file is up2date and if not, it will update it.

Just include `manageprojects` as a dev dependency in your project.
And add a test like this:

```python
class IncludeSetupPythonTestCase(IncludeSetupPythonBaseTestCase):

    # Set the path where the `setup_python.py` should be copied to:
    DESTINATION_PATH = Path(your_package.__file__).parent) / 'setup_python.py'

    # The test will pass, if the file is up2date, if it's update the script!
    def test_setup_python_is_up2date(self):
        self.auto_update_setup_python()
```

Feel free to do it in a completely different way, this is just a suggestion ;)

## Workflow - 1. Check system Python

If the system Python is the same major version as the required Python, we skip the download.

The script just returns the path to the system Python interpreter.

A local installed interpreter (e.g. in "~/.local") will be auto updated.

## Workflow - 2. Collect latest release data

We fetch the latest release data from the GitHub API:
https://raw.githubusercontent.com/indygreg/python-build-standalone/latest-release/latest-release.json

## Workflow - 3. Obtaining optimized Python distribution

See: https://gregoryszorc.com/docs/python-build-standalone/main/running.html

We choose the optimized variant based on the priority list:

1. `pgo+lto`
2. `pgo`
3. `lto`

For `x86-64` Linux we check the CPU flags from `/proc/cpuinfo` to determine the best variant.

The "debug" build are ignored.

## Workflow - 4. Check existing Python

If the latest Python version is already installed, we skip the download.

## Workflow - 4. Download and verify Archive

All downloads will be done with a secure connection (SSL) and server authentication.

We check if we have "zstd" or "gzip" installed for decompression and prefer "zstd" over "gzip".

If the latest Python version is already installed, we skip the download.

Download will be done in a temporary directory.

We check the file hash after downloading the archive.

## Workflow - 5. Add info JSON

We add the file `info.json` with all relevant information.

## Workflow - 6. Setup Python

We add a shell script to `~/.local/bin/pythonX.XX` to start the Python interpreter.

We display version information from Python and pip on `stderr`.

There exists two different directory structures:

* `./python/install/bin/python3`
* `./python/bin/python3`

We handle both cases and move all contents to the final destination.

The extracted Python will be moved to the final destination in `~/.local/pythonX.XX/`.

The script set's the correct `PYTHONHOME` environment variable.

## Workflow - 7. print the path

If no errors occurred, the path to the Python interpreter will be printed to `stdout`.
So it's usable in shell scripts, like:

```shell
#!/usr/bin/env sh

set -e

PY_313_BIN=$(python3 setup_python.py -v 3.13)
echo "Python 3.13 used from: '${PY_313_BIN}'"

set -x

${PY_313_BIN} -VV

```