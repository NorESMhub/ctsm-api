#!/usr/bin/env bash

set -e

source /ctsm-api/docker/entrypoint_setup.sh

sudo -s -E -u "$USER" bash <<EOF

cd /ctsm-api

./scripts/migrations_forward.sh

if [[ ${DEBUG:-0} == 1 ]]; then
  uvicorn app.main:app --reload --host 0.0.0.0
else
  uvicorn app.main:app --host 0.0.0.0
fi

EOF
