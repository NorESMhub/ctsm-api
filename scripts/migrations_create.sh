#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

alembic revision --autogenerate -m "${@}"
