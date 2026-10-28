#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
python3 -m venv --clear /opt/study5-verify
/opt/study5-verify/bin/python -m pip install --no-cache-dir --no-deps \
  --index-url http://127.0.0.1:3141/student/lab/+simple/ study5-hello-lab==0.1.0
cd /tmp
/opt/study5-verify/bin/python -I -c 'from study5_hello import hello; from importlib.metadata import version; print("Version:", version("study5-hello-lab")); print(hello())'
