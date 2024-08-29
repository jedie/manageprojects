#!/usr/bin/env sh

set -e

PY_312_BIN=$(python3 install_python.py -v 3.12)
echo "Python 3.12 used from: '${PY_312_BIN}'"

set -x

${PY_312_BIN} -VV
