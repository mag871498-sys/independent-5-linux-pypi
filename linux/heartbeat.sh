#!/bin/bash
set -euo pipefail
while true; do
    printf '%s mytest працює\n' "$(date --iso-8601=seconds)" | tee -a /tmp/test.log
    sleep 60
done
