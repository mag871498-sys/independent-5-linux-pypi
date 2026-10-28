#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
# Two workers, at most 50 runs each; fail the command if any scenario fails.
molotov -c -w 2 -d 3 -r 50 --delay 0.05 -f 1 loadtest.py
