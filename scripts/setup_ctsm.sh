#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

python app/utils/dependencies.py

rsync -rv resources/overwrites/ resources/ctsm
