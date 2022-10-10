#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

python app/utils/dependencies.py

# If resources/overwrites/ exists, run rsync
if [[ -d resources/overwrites ]]; then
  rsync -rv resources/overwrites/ resources/ctsm
fi
