#!/usr/bin/env bash

set -e

USER=root
HOME=/root

if [[ $HOST_USER && $HOST_UID ]]; then
  id -u "$HOST_USER" &>/dev/null || adduser --disabled-password --uid "$HOST_UID" "$HOST_USER"
  chown -R "$HOST_USER":"$HOST_USER" /ctsm-api/resources
  USER="$HOST_USER"

  cat >>/home/$USER/.bashrc <<EOF

export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77

EOF

export HOME=/home/$USER
export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77

ln -s /ctsm-api/resources/dotcime /home/$USER/.cime

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
