#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'

echo "AEGISX development environment is ready."
echo "Activate it with: source .venv/bin/activate"
