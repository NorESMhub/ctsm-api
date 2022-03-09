#!/usr/bin/env bash

set -e

cd /ctsm-api

./scripts/setup_ctsm.sh
./scripts/migrations_forward.sh

uvicorn app.main:app --reload --host 0.0.0.0
