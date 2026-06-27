#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python >/dev/null 2>&1; then
  echo "Error: python is not installed or not in PATH."
  exit 1
fi

if ! python -c "import pytest" >/dev/null 2>&1; then
  echo "pytest is not installed."
  echo "Install dev dependencies with:"
  echo "  pip install -r requirements-dev.txt"
  exit 1
fi

python -m pytest -q
