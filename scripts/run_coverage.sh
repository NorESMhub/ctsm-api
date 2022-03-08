#! /bin/bash

set -e

./scripts/run_tests.sh --cov=app --cov-report=term-missing --cov-report=html
