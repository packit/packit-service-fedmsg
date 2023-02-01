#!/usr/bin/bash

set -eu

DEFAULT_LIVENESS_FILE="/tmp/liveness"
LIVENESS_FILE="${LIVENESS_FILE:-$DEFAULT_LIVENESS_FILE}"

DEFAULT_LIVENESS_TIMEOUT="5"
LIVENESS_TIMEOUT="${LIVENESS_TIMEOUT:-$DEFAULT_LIVENESS_TIMEOUT}"

if [[ ! -f "${LIVENESS_FILE}" ]]; then
  echo "${LIVENESS_FILE} does not exist (yet?)"
  exit 0
fi

if [[ $(find "${LIVENESS_FILE}" -mmin "+${LIVENESS_TIMEOUT}" -print) ]]; then
  echo "${LIVENESS_FILE} is older than ${LIVENESS_TIMEOUT} minutes"
  exit 1
fi

echo "I am alive :)"
