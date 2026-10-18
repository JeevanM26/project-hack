#!/usr/bin/env bash
# J.A.R.V.I.S. Cross-Platform Root Launcher - macOS Edition
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR/mac"
chmod +x run.sh
./run.sh
