#!/bin/bash

set -e

uvicorn app.main:app --reload
