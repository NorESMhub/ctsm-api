#! /bin/bash

set -e

PROJECT_ROOT=$(dirname $(dirname $(realpath $0)))

export PYTHONPATH=$PROJECT_ROOT

python app/utils/dependencies.py

rsync -rv resources/overwrites/ resources/ctsm
