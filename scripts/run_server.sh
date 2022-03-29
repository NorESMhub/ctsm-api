#!/bin/bash

set -e

DEBUG=0
while test $# -gt 0; do
    case "$1" in
    -d | --debug)
        DEBUG=1
        shift
        ;;
    esac
done

DOCKER_COMPOSE_FILE=docker-compose.yaml
if [[ $DEBUG == 1 ]]; then
    DOCKER_COMPOSE_FILE=docker-compose.dev.yaml
fi
echo "Using $DOCKER_COMPOSE_FILE"

PROJECT_ROOT=$(dirname $(dirname $(realpath $0)))

cd $PROJECT_ROOT

docker-compose -f $DOCKER_COMPOSE_FILE up
