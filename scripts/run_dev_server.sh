#!/bin/bash

set -e

Swatchmedo auto-restart --directory=./app --pattern="*.py" --recursive -- celery -A app.tasks worker -E --loglevel DEBUG &
uvicorn app.main:app --reload
