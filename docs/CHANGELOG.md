# Changelog

## [Unreleased]

### Changed

- UX bỏ tab Setup.
- UX bỏ tab Verify riêng.
- Sidebar còn 7 tab.
- Workspace tự động nằm trong `APP_ROOT/workspace`.
- Tool bundled nằm trong `tools/`.
- Unpack tab chuyển sang Partition Explorer.
- Repack tab đổi thành `Repack & Verify` và tự chạy verify offline.
- Runbooks được đồng bộ với logic khóa: editable staging, Apply diff vào `modified/*.img`, Rebuild Super từ `lpdump`, verify RKFW header/MD5 tail.
- GUI PySide6 được refactor theo screenshots: shell Windows 11 style, sidebar icon/active state, cards, badges, warnings, tables, checklists và LogPanel cho đủ 7 tab.
- Project/Unpack/Analyze/Edit ROM Folder/Apply Changes/Rebuild Super/Repack & Verify hiện dùng mock UI đầy đủ, chưa gọi backend ROM thật.
- `TASK-0200` review PASS và chuyển sang DONE; xác nhận GUI mock không gọi WSL/subprocess/tool thật.

### Added

- `docs/TECHNICAL_KNOWLEDGE_BASE.md`.
- `docs/COMMANDS_REFERENCE.md`.
- `docs/architecture/PARTITION_EXPLORER_FLOW.md`.
- `docs/runbooks/03_UNPACK_SELECTED_IMAGE.md`.
- Chi tiết workspace tự động, bundled tools read-only, cảnh báo AVB/vbmeta, và câu kết quả verify offline được phép báo.
- `core/app_paths.py` detect `APP_ROOT` cho Python/EXE và tạo workspace dirs tự động.
- Test coverage cho `core/app_paths.py`: Python mode, frozen EXE mode, và `ensure_workspace()`.
- Mapping ảnh reference chi tiết trong `docs/design/UI_REFERENCE.md`.
- `core/tool_config.py` load bundled tool paths từ `APP_ROOT/tools` và báo `OK`/`MISSING`.
- `tests/test_tool_config.py` coverage cho bundled tools OK, missing và sai loại path.
- `TASK-0101B` review PASS và chuyển sang DONE; xác nhận không gọi WSL/subprocess/tool thật.
- `core/wsl_runner.py` với `WslRunner`, stream stdout/stderr realtime, result/exit code rõ ràng, failure/timeout errors.
- `tests/test_wsl_runner.py` mock subprocess coverage cho success, failure, stderr/stdout capture và timeout.
- `TASK-0102` review PASS và chuyển sang DONE; xác nhận production subprocess chỉ nằm trong `core/wsl_runner.py`.
