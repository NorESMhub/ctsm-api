#! /bin/bash

set -e

python app/utils/dependencies.py

rsync -rv resources/overwrites/ resources/ctsm
