#!/usr/bin/env bash

set -e
set -o pipefail

# Set the application to the $APPLICATION environment variable, or the 1st argument
# to the script if that isn't set.
APPLICATION=${APPLICATION-$1}
# If neither of the above is set, then use data_prep
APPLICATION=${APPLICATION-data_prep}

ARGS_FILE="${ARGS_FILE-/var/run/container_args}"

# if the command line arguments file exists, then use that
if [[ -f $ARGS_FILE ]]; then
    cat $ARGS_FILE | xargs /usr/bin/$APPLICATION
else
    exec /usr/bin/$APPLICATION ${@:2}
fi