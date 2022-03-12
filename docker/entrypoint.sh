#!/usr/bin/env bash

set -e

echo $HOST_USER
echo $HOST_UID

if [[ $HOST_USER && $HOST_UID ]]; then
  id -u "$HOST_USER" &>/dev/null || adduser --disabled-password --no-create-home --uid "$HOST_UID" "$HOST_USER"
  chown -R "$HOST_USER":"$HOST_USER" /ctsm-api/resources
  export USER="$HOST_USER"
fi

sudo -s -u "$USER" bash <<EOF

cd /ctsm-api

./scripts/setup_ctsm.sh
./scripts/migrations_forward.sh

celery -A app.tasks worker -E --loglevel INFO &
uvicorn app.main:app --reload --host 0.0.0.0

EOF
