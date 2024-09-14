#!/usr/bin/env sh

set -e

PY_313_BIN=$(python3 setup_python.py -v 3.13)
echo "Python 3.13 used from: '${PY_313_BIN}'"

set -x

${PY_313_BIN} -VV
