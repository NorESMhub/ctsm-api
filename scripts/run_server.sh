#!/bin/bash

set -e

DEBUG=0
BUILD=1
while test $# -gt 0; do
  case "$1" in
  -d | --debug)
    DEBUG=1
    shift
    ;;
  esac
  case "$1" in
  -b | --build)
    BUILD=1
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

if [[ $BUILD == 1 ]]; then
  docker-compose -f $DOCKER_COMPOSE_FILE build api
else
  docker-compose -f $DOCKER_COMPOSE_FILE up
fi
