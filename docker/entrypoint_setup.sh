#!/usr/bin/env bash

set -e

USER=root
HOME=/root

if [[ $HOST_USER && $HOST_UID ]]; then
  id -u "$HOST_USER" &>/dev/null || adduser --quiet --disabled-password --gecos "" --uid "$HOST_UID" "$HOST_USER"
  chown -R "$HOST_USER":"$HOST_USER" /ctsm-api/resources
  USER="$HOST_USER"
  HOME="/home/$HOST_USER"
fi

cat >>"$HOME"/.bashrc <<EOF

export USER="$USER"
export PYTHONPATH=/ctsm-api
export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77
# if CESMDATAROOT is changed, also change in entrypoint_setup.sh and other relevant places.
export CESMDATAROOT=/ctsm-api/resources/data/shared

EOF

export USER=$USER
export HOME=$HOME
export PYTHONPATH=/ctsm-api
export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77
# if CESMDATAROOT is changed, also change in entrypoint_setup.sh and other relevant places.
export CESMDATAROOT=/ctsm-api/resources/data/shared

ln -fs /ctsm-api/docker/dotcime "$HOME"/.cime
