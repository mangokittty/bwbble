#!/usr/bin/env bash

set -e
set -o pipefail

ARGS_FILE="${ARGS_FILE-/var/run/container_args}"

# if the command line arguments file exists, then use that
if [[ -f $ARGS_FILE ]]; then
    cat $ARGS_FILE | xargs /usr/bin/bwbble
else
    exec /usr/bin/bwbble $@
fi