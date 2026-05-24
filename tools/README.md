# APP_ROOT/tools

This folder is the only bundled tool location used by the app runtime.
Runtime code must resolve it through `core/app_paths.py` and
`core/tool_config.py`; users must not choose tool paths manually in the GUI.

The external tool folder at `/mnt/g/codex/tools` is only a source folder for
normalizing an existing local setup. It is not used by runtime code.

Normalize existing tools:

```bash
bash scripts/normalize_existing_tools.sh /mnt/g/codex/tools
```

The normalize script prefers tools from the provided source folder. If an
`lptools` binary is missing there, it also checks the current WSL `PATH` before
falling back to any `fakebin` stub.

Check the current bundled tool layout:

```bash
bash scripts/check_tools.sh
```

Expected layout:

```text
tools/afptool-rs/afptool-rs
tools/lptools/simg2img
tools/lptools/lpdump
tools/lptools/lpunpack
tools/lptools/lpmake
tools/avbtool/avbtool.py
```

Backend commands run inside WSL Linux. Do not place Windows `.exe` tools here
for backend use.

If `fakebin` tools are copied by the normalize script, they are stubs for
detection/tests only and must not be used on a real ROM.
