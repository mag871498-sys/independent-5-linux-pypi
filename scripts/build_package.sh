#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
python -m build
python -m twine check dist/*
