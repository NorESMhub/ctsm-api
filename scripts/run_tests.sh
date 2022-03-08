#!/bin/bash

set -e

export PYTHON_TEST=true

pytest app/tests "${@}"
