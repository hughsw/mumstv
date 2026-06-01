#!/bin/dash

set -x

exec ./mumstream/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --no-use-colors --reload
