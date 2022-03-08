#! /bin/bash

export PYTHONPATH=$PWD

if [[ -z "$1" ]]; then
  echo "Specify the revision to reverse to."
  exit 1
fi

# Run migrations
alembic downgrade "$1"
