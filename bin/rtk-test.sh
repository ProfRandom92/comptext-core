#!/bin/bash
# bin/rtk-test.sh
# Run pytest tests through the RTK (Rust Token Killer) proxy if available

if command -v rtk &> /dev/null; then
    echo "Running tests via RTK Token Killer Proxy..."
    rtk run python -m pytest -v "$@"
else
    echo "RTK proxy not found. Running standard pytest..."
    python -m pytest -v "$@"
fi
