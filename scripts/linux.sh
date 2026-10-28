#!/bin/bash
set -euo pipefail
if [[ $# -eq 0 ]]; then
    exec docker exec -it independent-5-linux-pypi /bin/bash
fi
exec docker exec independent-5-linux-pypi "$@"
