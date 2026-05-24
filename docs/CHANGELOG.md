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
- `TASK-0001` review PASS và chuyển sang DONE; xác nhận docs phản ánh đúng UX 7 tab, Partition Explorer, workspace tự động, bundled tools và no-flash MVP.
- `TASK-0101` review PASS và chuyển sang DONE; xác nhận `core/app_paths.py` detect `APP_ROOT` Python/EXE và tạo workspace tự động.
- `TASK-0103` implement xong và chuyển sang REVIEW; chỉ xử lý path conversion/quoting, không gọi WSL/subprocess/tool thật.
- `TASK-0103` review portable path conversion PASS và chuyển sang DONE.
- `TASK-0104` implement xong và chuyển sang REVIEW; chỉ xử lý RKFW header/MD5 tail bằng Python thuần, không gọi WSL/subprocess/tool thật.
- `TASK-0104` review PASS và chuyển sang DONE; ghi nhận non-blocker cho validate MD5 tail hex và guard output trùng repacked ở task sau.
- `TASK-0203` implement xong và chuyển sang REVIEW; image detector chỉ scan filesystem bằng Python thuần, không gọi WSL/subprocess/tool thật.
- `TASK-0203` review PASS và chuyển sang DONE; ghi nhận non-blocker thêm cảnh báo riêng khi sửa/rebuild `super.img` ở task sau.
- `TASK-0204` implement xong và chuyển sang REVIEW; AVB/vbmeta parser chỉ parse text report mẫu, không gọi WSL/subprocess/tool thật.
- `TASK-0204` review PASS và chuyển sang DONE; ghi nhận non-blocker workflow chạy avbtool thật phải qua `WslRunner` và GUI Analyze phải cảnh báo đỏ khi có Hash/Hashtree descriptor.
- `TASK-0205`, `TASK-0206`, `TASK-0207` implement xong và chuyển sang REVIEW; super.img metadata foundation chỉ detect/parse/build preview, chưa chạy tool thật.

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
- `core/path_utils.py` với `WindowsPathToWsl`, `windows_path_to_wsl()`, `shell_quote()` và `PathConversionError`.
- `tests/test_path_utils.py` coverage cho drive C, drive D, path có dấu cách, Unicode, WSL UNC path, shell quote và invalid path.
- UNC network path detection trong `core/path_utils.py`, trả lỗi rõ ràng rằng UNC network path chưa hỗ trợ trong MVP và cần copy file vào workspace local.
- `tests/test_path_utils.py` bổ sung coverage cho drive E và UNC network path NAS/IP.
- `core/rkfw.py` với helpers đọc/copy header RKFW tại offset `0x15`, đọc/tính/verify/ghi MD5 tail 32 byte và fix header+tail final.
- `tests/test_rkfw_md5.py` coverage cho header, MD5 tail, verify true/false, rewrite tail, fix header+tail và lỗi file quá nhỏ.
- `core/image_detector.py` với `scan_image_dir()`/`detect_images()` và metadata cho image trong RKAF `Image/`.
- `tests/test_image_detector.py` coverage cho known images, unknown `.img`, empty folder và no WSL/subprocess/tool calls.
- `core/avb.py` với `AvbInfo`, `AvbDescriptor`, parser text report, risk classifier và warning AVB descriptor.
- `tests/test_avb.py` và fixtures vbmeta text cho no-descriptor và Hash/Hashtree descriptor cases.
- `core/sparse_image.py` detect Android sparse magic bằng Python thuần.
- `core/lpdump_parser.py` parse lpdump text thành super metadata, dynamic groups và dynamic partitions.
- `core/lpmake_builder.py` build lpmake command preview từ parsed metadata, có group-size validation và shell-quoted preview string.
- `tests/test_sparse_image.py`, `tests/test_lpdump_parser.py`, `tests/test_lpmake_builder.py`.
- Expanded lpdump fixtures for RK3318 A/B and non-A/B layouts.
