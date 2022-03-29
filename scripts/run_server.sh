#!/bin/bash

set -e

DOCKER_COMPOSE_FILE=docker-compose.yaml
if [[ ${DEBUG:-0} == 1 ]]; then
    DOCKER_COMPOSE_FILE=docker-compose.dev.yaml
fi

echo "Using $DOCKER_COMPOSE_FILE"

PROJECT_ROOT=$(dirname $(dirname $(realpath $0)))

cd $PROJECT_ROOT

docker-compose -f $DOCKER_COMPOSE_FILE up
