#!/bin/bash

set -euo pipefail

trap 'rc=$?;set +ex;if [[ $rc -ne 0 ]];then trap - ERR EXIT;echo 1>&2;echo "*** fail *** : code $rc : $DIR/$SCRIPT $ARGS" 1>&2;echo 1>&2;exit $rc;fi' ERR EXIT
ARGS="$*"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(basename "${BASH_SOURCE[0]}")"

set -x

venv_dir=mumscamera

python3 -m venv ${venv_dir} --system-site-packages --upgrade-deps

${venv_dir}/bin/pip3 install "fastapi[standard-no-fastapi-cloud-cli]"
