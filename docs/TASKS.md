# TASKS

## Phase 0 — Docs & structure

### TASK-0001 — Update repo structure after UX change
Status: REVIEW
Owner: Implementer / Reviewer

Scope:
- Bỏ Setup/Verify riêng trong docs và GUI plan.
- Thêm Partition Explorer flow.
- Thêm `Repack & Verify` gộp verify offline.
- Cập nhật cây thư mục.
- Đồng bộ docs với logic khóa: workspace tự động, bundled tools, WSL-only backend, editable staging, Apply diff, Rebuild Super từ `lpdump`, RKFW header/MD5 verify.

Acceptance:
- Có docs mới phản ánh 7 tab.
- Có `PARTITION_EXPLORER_FLOW.md`.
- Có runbook `03_UNPACK_SELECTED_IMAGE.md`.
- Runbooks mô tả đúng `editable/<partition>`, `parts/`, `modified/`.
- Docs nêu rõ GUI không gọi subprocess trực tiếp và không cho chọn workspace/tool path.
- Docs nêu rõ `lpmake` phải parse từ `lpdump` gốc, không hard-code.
- Docs nêu đúng câu kết quả verify offline được phép báo.

## Phase 1 — Core foundation

### TASK-0101 — Implement `core/app_paths.py`
Status: REVIEW

Acceptance:
- Detect `APP_ROOT` khi chạy Python hoặc EXE.
- Tạo `workspace/projects`, `workspace/output`, `workspace/logs`, `workspace/temp`.
- Test `test_app_paths.py` pass.

### TASK-0101B — Implement bundled tool detection
Status: DONE

Scope:
- Implement `core/tool_config.py`.
- Dựa trên `core/app_paths.py` để xác định `APP_ROOT/tools`.
- Không cho người dùng chọn tool path.
- Không gọi WSL, không chạy tool thật.
- Chỉ kiểm tra sự tồn tại/path dự kiến của bundled tools.

Acceptance:
- Có hàm/class load bundled tool paths.
- Trả về trạng thái `OK`/`MISSING` cho từng tool:
  - `tools/afptool-rs/`
  - `tools/lptools/lpunpack`
  - `tools/lptools/lpmake`
  - `tools/lptools/lpdump`
  - `tools/avbtool/avbtool.py`
- Có kiểm tra missing tool rõ ràng.
- Không hard-code absolute path ngoài `APP_ROOT`.
- `tests/test_tool_config.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Reviewer notes:
- PASS: `core/tool_config.py` chỉ kiểm tra paths dưới `AppPaths.tools_dir`.
- PASS: Không hard-code absolute path ngoài `APP_ROOT`; mọi tool dùng relative path dưới `tools/`.
- PASS: Không có cơ chế cho người dùng chọn tool path.
- PASS: Kiểm tra đủ `afptool-rs/`, `lptools/lpunpack`, `lptools/lpmake`, `lptools/lpdump`, `avbtool/avbtool.py`.
- PASS: `afptool-rs` được kiểm tra là directory; các tool còn lại là file.
- PASS: Mỗi tool trả về trạng thái `OK` hoặc `MISSING`, có `missing_tools` rõ ràng.
- PASS: Không gọi WSL, subprocess hoặc tool thật.
- PASS: Tests cover all OK, missing tools và `afptool-rs` sai loại path.

### TASK-0102 — Implement `core/wsl_runner.py`
Status: DONE

Acceptance:
- Đây là nơi duy nhất gọi `wsl.exe`.
- Hỗ trợ stream log realtime.
- Test mock subprocess pass.
- Có command builder dạng `wsl.exe bash -lc <command>` và không hard-code distro Ubuntu.
- Trả exit code rõ ràng.
- Không nuốt stderr; stdout/stderr được capture rõ ràng.
- Có error class khi command fail.
- Có timeout handling.
- `tests/test_wsl_runner.py` pass.

Reviewer notes:
- PASS: Production code chỉ gọi `subprocess`/`wsl.exe` trong `core/wsl_runner.py`; GUI không gọi subprocess.
- PASS: Command builder mặc định đúng dạng `wsl.exe bash -lc <command>`.
- PASS: Không hard-code Ubuntu; distro optional qua tham số `distro`.
- PASS: stdout và stderr được capture riêng, không nuốt stderr.
- PASS: stdout/stderr được stream từng dòng qua callback `on_output`.
- PASS: `WslCommandResult` trả `exit_code` rõ ràng.
- PASS: Non-zero exit code raise `WslCommandError` khi `check=True`; `check=False` trả result.
- PASS: Timeout raise `WslCommandTimeout` và kill process.
- PASS: Tests dùng mock subprocess, không phụ thuộc WSL thật; cover builder, success, failure, `check=False`, stdout/stderr capture và timeout.

## Phase 2 — Project & Unpack GUI

### TASK-0200 — Refactor GUI mock UI from screenshots
Status: DONE

Scope:
- Refactor PySide6 GUI theo ảnh reference trong `docs/design/screenshots/`.
- Sidebar hiện đại, có icon, active state, đúng 7 tab.
- Mỗi tab có mock UI đầy đủ, không implement backend ROM thật.
- Không gọi WSL/subprocess/tool thật.

Acceptance:
- Giao diện không còn trống/sơ sài.
- Đủ 7 tab: Project, Unpack, Analyze, Edit ROM Folder, Apply Changes, Rebuild Super, Repack & Verify.
- Không có Setup tab hoặc Verify tab riêng.
- Workspace chỉ hiển thị tự động.
- Tools chỉ hiển thị bundled/read-only.
- Mỗi tab có LogPanel dưới cùng.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Reviewer notes:
- PASS: Sidebar có đúng 7 tab và đúng thứ tự: Project, Unpack, Analyze, Edit ROM Folder, Apply Changes, Rebuild Super, Repack & Verify.
- PASS: Không có Setup tab và không có Verify tab riêng.
- PASS: 7 tab đều dùng mock UI đầy đủ; `MainWindow` không còn mount `PlaceholderTab`.
- PASS: Project tab có chọn ROM gốc, tên project, APK tùy chọn, workspace tự động, bundled tools read-only và LogPanel.
- PASS: Unpack tab có Partition Explorer mock, step RKFW/RKAF/Detect images, bảng image mock và dynamic partitions.
- PASS: Analyze/Edit/Apply/Rebuild/Repack tabs có đủ card, table, checklist, warning và LogPanel theo scope.
- PASS: GUI không gọi subprocess, WSL hoặc tool thật; task chỉ hiển thị mock data.
- PASS: Tests pass: `python -m compileall .`, `python app.py --smoke-test`, `python -m pytest`, GUI instantiate offscreen 7 tab đúng thứ tự.

### TASK-0201 — Project tab MVP
Status: TODO

### TASK-0202 — Unpack tab Partition Explorer mock
Status: TODO

### TASK-0203 — Image detector core
Status: TODO
