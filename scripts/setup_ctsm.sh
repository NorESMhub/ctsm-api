#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

python app/utils/dependencies.py
