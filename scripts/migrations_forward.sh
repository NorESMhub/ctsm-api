#! /bin/bash

export PYTHONPATH=$PWD

# Forward migrations to the given revision. Default to `head` if a revision is not passed.
alembic upgrade "${1:-head}"
