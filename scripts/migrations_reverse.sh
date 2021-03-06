#! /bin/bash

set -e

export PYTHONPATH=$(dirname $(dirname $(realpath $0)))

if [[ -z "$1" ]]; then
  echo "Specify the revision to reverse to."
  exit 1
fi

# Run migrations
alembic downgrade "$1"
