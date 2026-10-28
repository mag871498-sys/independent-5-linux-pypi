#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
export NO_COLOR=1
python -m build
python -m twine check dist/*
