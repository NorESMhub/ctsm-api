#!/bin/bash

set -x

FIX=0

while test $# -gt 0; do
    case "$1" in
    -f | --fix)
        FIX=1
        shift
        ;;
    esac
done

mypy app

if [[ $FIX == 1 ]]; then
    # Sort imports one per line, so autoflake can remove unused imports
    isort --force-single-line-imports alembic app
    autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place --exclude=__init__.py alembic app
    # Now sort imports properly
    isort alembic app
    black alembic app
else
    black --check alembic app
    isort --check-only alembic app
    flake8
fi
