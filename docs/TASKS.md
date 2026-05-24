# TASKS

## Phase 0 — Docs & structure

### TASK-0001 — Update repo structure after UX change
Status: DONE
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

Reviewer notes:
- PASS: Docs phản ánh đúng 7 tab: Project, Unpack, Analyze, Edit ROM Folder, Apply Changes, Rebuild Super, Repack & Verify.
- PASS: Docs nêu rõ không có Setup tab và không có Verify tab riêng.
- PASS: Có `PARTITION_EXPLORER_FLOW.md` và runbook `03_UNPACK_SELECTED_IMAGE.md`.
- PASS: Repack & Verify gộp verify offline, chỉ báo `Verify offline PASS` và không claim ROM chắc chắn boot.
- PASS: Workspace tự động và bundled tools read-only được mô tả trong spec/runbooks.
- PASS: Docs có editable staging, Apply diff bằng `debugfs`, Rebuild Super từ `lpdump` và Repack & Verify.
- PASS: MVP không flash thiết bị.

## Phase 1 — Core foundation

### TASK-0101 — Implement `core/app_paths.py`
Status: DONE

Acceptance:
- Detect `APP_ROOT` khi chạy Python hoặc EXE.
- Tạo `workspace/projects`, `workspace/output`, `workspace/logs`, `workspace/temp`.
- Test `test_app_paths.py` pass.

Reviewer notes:
- PASS: `core/app_paths.py` detect `APP_ROOT` khi chạy Python từ thư mục chứa `app.py`.
- PASS: Detect `APP_ROOT` khi frozen EXE bằng thư mục chứa `sys.executable`.
- PASS: Workspace tự động nằm trong `APP_ROOT/workspace`.
- PASS: `ensure_workspace()` tạo đủ `workspace/projects`, `workspace/output`, `workspace/logs`, `workspace/temp`.
- PASS: Không gọi WSL/subprocess và không có cơ chế cho người dùng chọn workspace thủ công.
- PASS: `tests/test_app_paths.py` pass.

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

### TASK-0103 — Implement `core/path_utils.py`
Status: DONE

Scope:
- Chuyển Windows path sang WSL path.
- Quote shell path an toàn.
- Không gọi WSL.
- Không gọi subprocess.
- Không gọi ROM tool thật.

Acceptance:
- Convert `C:\Users\Test\rom.img` -> `/mnt/c/Users/Test/rom.img`.
- Convert `D:\ROM_BOX\update.img` -> `/mnt/d/ROM_BOX/update.img`.
- Hỗ trợ path có dấu cách.
- Hỗ trợ Unicode tiếng Việt.
- Có `shell_quote()`.
- Có error rõ ràng nếu path không hợp lệ.
- `tests/test_path_utils.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `WindowsPathToWsl`, `windows_path_to_wsl()`, `shell_quote()` and `PathConversionError`.
- Supports drive-letter paths, paths with spaces, Unicode paths and WSL UNC paths like `\\wsl$\Ubuntu-24.04\home\user\project`.
- Does not call WSL, subprocess or ROM tools.
- Tests pass: `tests/test_path_utils.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: Conversion is portable across Windows drive letters and does not hard-code C:, D:, username, workspace or machine name.
- PASS: Converts C/D/E drive examples to `/mnt/<drive>/...`, including paths with spaces and Unicode tiếng Việt.
- PASS: `shell_quote()` uses POSIX shell quoting and safely quotes `/mnt/d/ROM Box/update.img`.
- PASS: WSL UNC paths are detected and converted to Linux paths; UNC network paths raise a clear MVP error asking the user to copy into local workspace.
- PASS: Relative/invalid paths raise `PathConversionError` instead of returning ambiguous output.
- PASS: No WSL, subprocess, GUI or ROM tool calls were added.
- PASS: Tests pass: `tests/test_path_utils.py`, `compileall`, smoke test and full pytest.

### TASK-0104 — Implement `core/rkfw.py` RKFW header and MD5 tail utilities
Status: DONE

Scope:
- Implement RKFW header and MD5 tail helpers in `core/rkfw.py`.
- Use Python binary file I/O only.
- Do not call WSL, subprocess, `afptool-rs` or any ROM tool.
- Do not unpack/repack a real ROM and do not modify GUI.

Acceptance:
- `read_rkfw_header(path) -> bytes` reads 4 bytes at offset `0x15`.
- `copy_rkfw_header(original_path, target_path)` copies the original RKFW chip header into target.
- `read_md5_tail(path) -> str` reads the 32 byte ASCII MD5 tail.
- `compute_body_md5(path) -> str` hashes the file body excluding the final 32 bytes using chunks.
- `verify_md5_tail(path) -> bool` compares body MD5 with the tail.
- `rewrite_md5_tail(path) -> str` rewrites the final 32 byte ASCII MD5 tail.
- `fix_header_and_md5_tail(original_path, repacked_path, output_path)` copies repacked to output, restores header, recalculates MD5 tail and returns result info.
- Small files raise `RkfwImageError` with clear messages.
- `tests/test_rkfw_md5.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added constants for header offset/size and MD5 tail size.
- Added `RkfwImageError` and `RkfwFixResult`.
- MD5 calculation reads in chunks and does not load the full image into RAM.
- Tests cover header read/copy, tail read, body MD5, verify true/false, rewrite tail, fix header+tail and too-small file errors.
- No WSL, subprocess, GUI or ROM tool calls were added.
- Tests pass: `tests/test_rkfw_md5.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: `read_rkfw_header()` đọc đúng 4 byte tại offset `0x15`.
- PASS: `copy_rkfw_header()` copy header từ ROM gốc sang target.
- PASS: `read_md5_tail()` đọc 32 byte ASCII MD5 tail cuối file.
- PASS: `compute_body_md5()` tính MD5 body trừ 32 byte cuối bằng chunk, không load toàn bộ file vào RAM.
- PASS: `verify_md5_tail()` so sánh body MD5 với tail.
- PASS: `rewrite_md5_tail()` ghi lại MD5 tail đúng.
- PASS: `fix_header_and_md5_tail()` copy repacked sang output, restore header gốc, tính lại MD5 tail và trả result.
- PASS: File quá nhỏ raise `RkfwImageError` rõ ràng.
- PASS: Không gọi WSL, subprocess, `afptool-rs`, không sửa GUI và không dùng ROM tool thật.
- PASS: Tests pass: `tests/test_rkfw_md5.py`, `compileall`, smoke test và full pytest.
- Non-blocker: Có thể thêm validate MD5 tail là 32 ký tự hex ở task sau.
- Non-blocker: Có thể thêm guard nếu `output_path` trùng `repacked_path` ở task sau.

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
Status: DONE

Scope:
- Implement `core/image_detector.py`.
- Scan unpacked RKAF `Image/` folder using Python filesystem APIs only.
- Detect known Rockchip/Android image files and unknown `.img` files.
- Do not call WSL, subprocess or ROM tools.
- Do not modify GUI.

Acceptance:
- Detect `super.img` as `dynamic_super` with actions `analyze`, `unpack`.
- Detect `vbmeta.img` as `avb_vbmeta` with action `analyze_avb`.
- Detect `boot.img` and `recovery.img` as analyze-only boot/recovery images.
- Detect `dtbo.img` as info-only.
- Detect `uboot.img` and `trust.img` as `bootloader_danger`, risk `danger`, info-only.
- Detect `misc.img` and `parameter.txt`.
- Detect unknown `.img` files as `unknown_image`.
- Empty `Image/` folder returns an empty list.
- No WSL, subprocess or ROM tool calls.
- `tests/test_image_detector.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `DetectedImage`, `ImageKind`, `ImageDetectorError`, `scan_image_dir()` and `detect_images()`.
- Returned metadata includes `name`, `path`, `size_bytes`, `type`, `risk_level` and `supported_actions`.
- Known files are sorted in Partition Explorer order; unknown `.img` files follow alphabetically.
- Non-image unrelated files are ignored.
- Tests use `tmp_path` and fake files only.
- Tests pass: `tests/test_image_detector.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: `core/image_detector.py` chỉ scan filesystem bằng Python thuần.
- PASS: Không gọi WSL, subprocess, ROM tool thật và không sửa GUI.
- PASS: Detect `super.img` là `dynamic_super`, actions `analyze`/`unpack`.
- PASS: Detect `vbmeta.img` là `avb_vbmeta`, action `analyze_avb`.
- PASS: Detect `boot.img`/`recovery.img` là analyze-only.
- PASS: Detect `dtbo.img` là info-only.
- PASS: Detect `uboot.img`/`trust.img` là `bootloader_danger`, risk `danger`, `info_only`.
- PASS: Detect `misc.img`, `parameter.txt` và unknown `.img`.
- PASS: Empty `Image/` folder trả list rỗng; missing/non-directory path raise `ImageDetectorError` rõ ràng.
- PASS: Metadata trả về đủ `name`, `path`, `size_bytes`, `type`, `risk_level`, `supported_actions`.
- PASS: Tests pass: `tests/test_image_detector.py`, `compileall`, smoke test và full pytest.
- Non-blocker: `super.img` risk `safe` chấp nhận được cho analyze/unpack; khi làm rebuild super/lpmake thật cần thêm cảnh báo riêng vì sửa `super.img` vẫn có rủi ro.

### TASK-0204 — Implement `core/avb.py` AVB/vbmeta info parser
Status: DONE

Scope:
- Implement `core/avb.py`.
- Parse text output from `info_image --image vbmeta.img` reports only.
- Do not call WSL, subprocess or any ROM tool.
- Do not parse binary `vbmeta.img` in this task.
- Do not modify GUI.

Acceptance:
- `parse_avb_info_text(text) -> AvbInfo`.
- `load_avb_info_report(path) -> AvbInfo`.
- `classify_avb_risk(info) -> str`.
- Parse `Algorithm`, `Flags`, `Rollback Index` and descriptor blocks.
- Parse safe/no-descriptor reports such as `Algorithm: NONE`, `Flags: 2`, `Descriptors: none`.
- Parse Hash descriptor partition metadata.
- Parse Hashtree descriptor partition metadata.
- Detect multiple descriptors and de-duplicate `affected_partitions`.
- `flags` parsed as `int`.
- Risk is `low` for no descriptors with likely disabled verification.
- Risk is `danger` when Hash/Hashtree descriptors exist.
- Empty or unrecognized text raises `AvbParseError`.
- No WSL, subprocess or real tool calls.
- `tests/test_avb.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `AvbInfo`, `AvbDescriptor` and `AvbParseError`.
- Parser reads report text only; real tool execution stays for a later workflow task via `WslRunner`.
- `warnings` explicitly warn when AVB descriptors may cause bootloop if modified partitions are not handled correctly.
- `affected_partitions` keeps detected partition names without hard-coding system/product/vendor only.
- Added fixtures `vbmeta_algorithm_none.txt` and `vbmeta_with_descriptors.txt`.
- Tests pass: `tests/test_avb.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: `core/avb.py` chỉ parse text report từ `avbtool info_image` output.
- PASS: Không gọi WSL, subprocess, `avbtool.py` thật, không đọc binary `vbmeta.img` thật và không sửa GUI.
- PASS: Có `AvbInfo`, `AvbDescriptor`, `AvbParseError`.
- PASS: Có `parse_avb_info_text(text)`, `load_avb_info_report(path)` và `classify_avb_risk(info)`.
- PASS: Parse được `Algorithm`, `Flags`, `Rollback Index`, Hash descriptor và Hashtree descriptor.
- PASS: Parse được `Partition Name`, `Image Size`, `Salt`, `Digest`/`Root Digest`.
- PASS: Detect `has_hash_descriptor`, `has_hashtree_descriptor`; `affected_partitions` không duplicate và không hard-code chỉ `system/product/vendor`.
- PASS: `Algorithm: NONE` + `Flags: 2` + `Descriptors: none` classify risk `low`.
- PASS: Có Hash/Hashtree descriptor classify risk `danger`.
- PASS: Empty/unrecognized text raise `AvbParseError` rõ ràng.
- PASS: Tests pass: `tests/test_avb.py`, `compileall`, smoke test và full pytest.
- Non-blocker: Workflow chạy `avbtool.py` thật phải làm ở task sau và đi qua `WslRunner`.
- Non-blocker: GUI Analyze tab sau này phải hiện cảnh báo đỏ nếu có Hash/Hashtree descriptor.
- Non-blocker: Không được kết luận chắc chắn AVB đã tắt, chỉ dùng wording `likely disabled` / `requires attention`.
