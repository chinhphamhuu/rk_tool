# PROJECT_STATE

## Trạng thái hiện tại

Đã chốt UX mới:

- Bỏ tab Setup.
- Bỏ tab Verify riêng.
- Tool bundled trong `tools/`.
- Workspace tự động trong `APP_ROOT/workspace/`.
- Sidebar còn 7 tab.
- Tab Unpack chuyển thành Partition Explorer.
- Tab Repack đổi thành `Repack & Verify`, tự verify offline sau khi repack.

Docs alignment đang ở REVIEW cho `TASK-0001`. `TASK-0101` đã implement `core/app_paths.py` và đang ở REVIEW. `TASK-0101B` đã review PASS và DONE. `TASK-0102` đã review PASS và DONE. `TASK-0200` đã review PASS và DONE.

## Review mới nhất

`TASK-0102 — Implement core/wsl_runner.py`:

- PASS: `core/wsl_runner.py` là nơi production duy nhất gọi `subprocess`/`wsl.exe`.
- PASS: GUI không gọi subprocess.
- PASS: Command builder dùng `wsl.exe bash -lc <command>` và distro optional, không hard-code Ubuntu.
- PASS: stdout/stderr được stream từng dòng, capture riêng và trả trong result.
- PASS: exit code rõ ràng; failure/timeout có error class riêng.
- PASS: Tests dùng mock subprocess, không phụ thuộc WSL thật.
- PASS: Tests pass: `test_wsl_runner.py`, `compileall`, smoke test và full pytest.

`TASK-0101B — Implement bundled tool detection`:

- PASS: Tool detection chỉ dùng `AppPaths.tools_dir` dưới `APP_ROOT/tools`.
- PASS: Không hard-code absolute path, không cho chọn tool path.
- PASS: Kiểm tra đủ bundled tools bắt buộc và phân biệt directory/file.
- PASS: Trạng thái `OK`/`MISSING` rõ ràng cho từng tool.
- PASS: Không gọi WSL, subprocess hoặc tool thật.
- PASS: Tests pass: `test_tool_config.py`, `compileall`, smoke test và full pytest.

`TASK-0200 — Refactor GUI mock UI from screenshots`:

- Sidebar đúng 7 tab, đúng thứ tự, có icon và active state.
- Không có Setup tab, không có Verify tab riêng.
- Mỗi tab có mock UI đầy đủ, không còn trang trắng trong stack chính.
- GUI không gọi subprocess, WSL hoặc tool thật.
- Workspace chỉ hiển thị tự động; tools chỉ hiển thị bundled/read-only.
- Tests pass: `compileall`, smoke test, pytest và GUI instantiate offscreen.

## Implementation mới nhất

`TASK-0102 — Implement core/wsl_runner.py`:

- `WslRunner` build command dạng `wsl.exe bash -lc <command>`.
- Không hard-code distro Ubuntu; distro là optional.
- Dùng `subprocess.Popen` trong duy nhất `core/wsl_runner.py`.
- Stream stdout/stderr từng dòng qua callback.
- Capture stdout/stderr riêng, không nuốt stderr.
- Trả `WslCommandResult` với `exit_code` rõ ràng.
- Raise `WslCommandError` khi command fail và `WslCommandTimeout` khi timeout.
- Tests dùng mock subprocess, không phụ thuộc WSL thật.

`TASK-0101B — Implement bundled tool detection`:

- `core/tool_config.py` load tool paths từ `AppPaths.tools_dir`.
- Kiểm tra bundled tools theo path tương đối dưới `APP_ROOT/tools`.
- Trả về trạng thái `OK` hoặc `MISSING` cho từng tool.
- Không gọi WSL, subprocess hoặc tool thật.
- Có test mock bằng `tmp_path` cho all-OK, missing tools và sai loại path.

## Kiến trúc đã khóa

- GUI PySide6.
- Backend WSL qua `core/wsl_runner.py`.
- GUI không gọi subprocess trực tiếp.
- Tool config tự động qua `core/app_paths.py` và `core/tool_config.py`.
- Không flash trong MVP.
- Không cho người dùng chọn workspace thủ công.
- Không cho người dùng chọn tool path trong GUI.
- Chỉ `core/wsl_runner.py` được gọi `wsl.exe`/subprocess.
- `super.img` phải rebuild từ metadata `lpdump` gốc, không hard-code `lpmake`.
- Editable folder chỉ là staging; Apply Changes phải copy `parts/*.img` sang `modified/*.img` rồi apply diff bằng `debugfs`.

## Rủi ro kỹ thuật đang mở

- AVB/vbmeta Hash descriptor hoặc Hashtree descriptor cần cảnh báo đỏ.
- Sai sparse/raw handling của `super.img` có thể làm lpdump/lpunpack fail.
- Sai metadata `lpmake` từ `lpdump` có thể tạo `super.img` không hợp lệ.
- Mất permission, owner, SELinux, xattr hoặc symlink khi apply diff có thể làm ROM lỗi.
- RKFW header tại offset `0x15` và MD5 tail 32 byte cuối file phải verify sau repack.

## Task tiếp theo đề xuất

1. Review `TASK-0001` docs alignment.
2. Review `TASK-0101` — `core/app_paths.py`.
3. Implement backend wiring cho Project/Unpack sau khi core foundation review xong.
