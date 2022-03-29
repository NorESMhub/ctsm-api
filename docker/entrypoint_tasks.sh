#!/usr/bin/env bash

set -e

source /ctsm-api/docker/entrypoint_setup.sh

sudo -s -E -u "$USER" bash <<EOF

cd /ctsm-api

if [[ ${DEBUG:-0} == 1 ]]; then
  watchmedo auto-restart --directory=./app --pattern="*.py" --recursive -- celery -A app.tasks worker -E --loglevel DEBUG
else
  celery -A app.tasks worker -E --loglevel INFO
fi

EOF
