#!/usr/bin/env bash

set -e

if [[ $HOST_USER && $HOST_UID ]]; then
  id -u "$HOST_USER" &>/dev/null || adduser --disabled-password --no-create-home --uid "$HOST_UID" "$HOST_USER"
  chown -R "$HOST_USER":"$HOST_USER" /ctsm-api/resources
  export USER="$HOST_USER"
fi

sudo -s -E -u "$USER" bash <<EOF

cd /ctsm-api

./scripts/setup_ctsm.sh
./scripts/migrations_forward.sh

if [[ $DEBUG && $DEBUG == 1 ]]; then
  watchmedo auto-restart --directory=./app --pattern="*.py" --recursive -- celery -A app.tasks worker -E --loglevel DEBUG &
  uvicorn app.main:app --reload --host 0.0.0.0
else
  celery -A app.tasks worker -E --loglevel INFO &
  uvicorn app.main:app --host 0.0.0.0
fi

EOF
