#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

# Forward migrations to the given revision. Default to `head` if a revision is not passed.
alembic upgrade "${1:-head}"
