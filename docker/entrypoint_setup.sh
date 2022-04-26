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
export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77

EOF

export USER=$USER
export HOME=$HOME
export CIME_MACHINE=container
export MPICC=mpicc
export MPIFC=mpif90
export MPIF90=mpif90
export MPIF77=mpif77

ln -fs /ctsm-api/resources/dotcime "$HOME"/.cime
