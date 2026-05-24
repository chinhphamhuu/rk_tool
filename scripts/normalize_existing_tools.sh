#!/usr/bin/env bash
set -u

SOURCE_TOOLS="${1:-../tools}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_TOOLS="${APP_ROOT}/tools"

mkdir -p \
  "${TARGET_TOOLS}/afptool-rs" \
  "${TARGET_TOOLS}/lptools" \
  "${TARGET_TOOLS}/avbtool"

copy_tool() {
  local name="$1"
  local source_path="$2"
  local target_path="$3"
  local note="${4:-}"

  if [[ -n "${source_path}" && -f "${source_path}" ]]; then
    cp -f "${source_path}" "${target_path}"
    chmod +x "${target_path}"
    if [[ "${note}" == "STUB" ]]; then
      echo "${name}: OK (STUB/FAKE copied from ${source_path})"
    else
      echo "${name}: OK (copied from ${source_path})"
    fi
    return 0
  fi

  echo "${name}: MISSING"
  return 1
}

first_existing_file() {
  local candidate
  for candidate in "$@"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

find_lp_tool() {
  local tool_name="$1"
  local candidate=""
  local note=""

  candidate="$(
    find \
      "${SOURCE_TOOLS}/lpunpack_and_lpmake" \
      "${SOURCE_TOOLS}/lpunpack_and_lmake" \
      -type f -name "${tool_name}" -print 2>/dev/null | head -n 1
  )"

  if [[ -z "${candidate}" ]]; then
    candidate="$(command -v "${tool_name}" 2>/dev/null || true)"
  fi

  if [[ -z "${candidate}" ]]; then
    candidate="$(
      find "${SOURCE_TOOLS}/fakebin" -maxdepth 2 -type f -name "${tool_name}" -print 2>/dev/null | head -n 1
    )"
    if [[ -n "${candidate}" ]]; then
      note="STUB"
    fi
  fi

  printf '%s\t%s\n' "${candidate}" "${note}"
}

echo "APP_ROOT: ${APP_ROOT}"
echo "SOURCE_TOOLS: ${SOURCE_TOOLS}"
echo "TARGET_TOOLS: ${TARGET_TOOLS}"

if [[ ! -d "${SOURCE_TOOLS}" ]]; then
  echo "Source tools folder not found: ${SOURCE_TOOLS}"
  exit 1
fi

afptool_source="$(
  first_existing_file \
    "${SOURCE_TOOLS}/afptool-rs-linux-x86_64_patched" \
    "${SOURCE_TOOLS}/afptool-rs-linux-x86_64" \
    "${SOURCE_TOOLS}/afptool-rs-src/target/release/afptool-rs" \
    || true
)"
copy_tool "afptool-rs" "${afptool_source}" "${TARGET_TOOLS}/afptool-rs/afptool-rs" || true

copy_tool "avbtool.py" "${SOURCE_TOOLS}/avbtool.py" "${TARGET_TOOLS}/avbtool/avbtool.py" || true

for tool_name in simg2img lpdump lpunpack lpmake; do
  IFS=$'\t' read -r source_path note < <(find_lp_tool "${tool_name}")
  copy_tool "${tool_name}" "${source_path}" "${TARGET_TOOLS}/lptools/${tool_name}" "${note}" || true
done

echo
echo "Run scripts/check_tools.sh to verify the normalized APP_ROOT/tools layout."
