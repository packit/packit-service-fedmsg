#!/usr/bin/bash

set -eu

if [[ ! -f "${LIVENESS_FILE:=/tmp/liveness}" ]]; then
  echo "${LIVENESS_FILE} does not exist (yet?)"
  exit 0
fi

: "${LIVENESS_TIMEOUT:=5}"
if [[ $(find "${LIVENESS_FILE}" -mmin "+${LIVENESS_TIMEOUT}" -print) ]]; then
  echo "${LIVENESS_FILE} is older than ${LIVENESS_TIMEOUT} minutes"
  exit 1
fi

echo "I am alive :)"
