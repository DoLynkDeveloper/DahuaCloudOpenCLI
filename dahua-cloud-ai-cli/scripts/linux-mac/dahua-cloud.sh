#!/usr/bin/env bash
# Linux/Mac 直接调用入口
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "${SCRIPT_DIR}/../../src/dahua-cloud-ai-cli.py" "$@"
