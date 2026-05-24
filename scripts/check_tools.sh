#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOLS_DIR="${APP_ROOT}/tools"

check_tool() {
  local name="$1"
  local path="$2"

  if [[ ! -e "${path}" ]]; then
    echo "${name}: MISSING"
    return 1
  fi

  if [[ ! -f "${path}" ]]; then
    echo "${name}: NOT_FILE"
    return 1
  fi

  if [[ ! -x "${path}" ]]; then
    echo "${name}: NOT_EXECUTABLE"
    return 1
  fi

  echo "${name}: OK"
  return 0
}

check_tool "afptool-rs" "${TOOLS_DIR}/afptool-rs/afptool-rs" || true
check_tool "simg2img" "${TOOLS_DIR}/lptools/simg2img" || true
check_tool "lpdump" "${TOOLS_DIR}/lptools/lpdump" || true
check_tool "lpunpack" "${TOOLS_DIR}/lptools/lpunpack" || true
check_tool "lpmake" "${TOOLS_DIR}/lptools/lpmake" || true
check_tool "avbtool.py" "${TOOLS_DIR}/avbtool/avbtool.py" || true

exit 0
