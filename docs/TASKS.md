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
  - `tools/afptool-rs/afptool-rs`
  - `tools/lptools/simg2img`
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

### TASK-0205 — Implement `core/sparse_image.py`
Status: DONE

Scope:
- Detect Android sparse image format with Python file I/O only.
- Do not call WSL, subprocess, `simg2img` or ROM tools.
- Do not modify GUI.

Acceptance:
- `read_magic(path) -> bytes` reads only the 4 byte header.
- `is_android_sparse_image(path) -> bool` detects magic `0xED26FF3A` stored as bytes `3A FF 26 ED`.
- `classify_image_format(path) -> str` returns `android_sparse` or `raw_or_unknown`.
- Missing or too-small files raise `SparseImageError` clearly.
- `tests/test_sparse_image.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `ANDROID_SPARSE_MAGIC`, `SparseImageError`, `read_magic()`, `is_android_sparse_image()` and `classify_image_format()`.
- Only the first 4 bytes are read; large images are not loaded into RAM.
- No WSL, subprocess, `simg2img`, GUI or ROM tool calls were added.
- Tests pass: `tests/test_sparse_image.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: `sparse_image.py` detects Android sparse magic `0xED26FF3A` / bytes `3A FF 26 ED`.
- PASS: Only reads the 4-byte header, not the full image into memory.
- PASS: Missing/tiny files raise `SparseImageError` clearly.
- PASS: Does not call WSL, subprocess, `simg2img`, or any real ROM tool.
- PASS: Tests pass: `tests/test_sparse_image.py`, `compileall`, smoke test, and full pytest.

### TASK-0206 — Implement `core/lpdump_parser.py`
Status: DONE

Scope:
- Parse text output from `lpdump` reports.
- Do not call WSL, subprocess, `lpdump` or ROM tools.
- Do not modify GUI.

Acceptance:
- `parse_lpdump_text(text) -> SuperMetadata`.
- `load_lpdump_report(path) -> SuperMetadata`.
- Parse metadata size, metadata slots, block size, device size and optional alignment.
- Parse dynamic groups with maximum size and flags.
- Parse dynamic partitions with name, group, size, readonly/attributes and extent count.
- Support A/B partitions such as `system_a`, `product_a`, `vendor_a`, `odm_a`, `system_ext_a`.
- Support non-A/B partitions such as `system`, `product`, `vendor`, `odm`, `system_ext`.
- Unknown partition names are preserved.
- Empty text or missing required fields raise `LpDumpParseError`.
- `tests/test_lpdump_parser.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `SuperMetadata`, `DynamicGroup`, `DynamicPartition`, `LpDumpParseError`, `parse_lpdump_text()` and `load_lpdump_report()`.
- Parser uses tolerant key/value and block scanning instead of a single rigid layout.
- Updated A/B and non-A/B fixtures with group and partition metadata.
- No WSL, subprocess, `lpdump`, GUI or ROM tool calls were added.
- Tests pass: `tests/test_lpdump_parser.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: Provides `SuperMetadata`, `DynamicGroup`, `DynamicPartition`, and `LpDumpParseError`.
- PASS: `parse_lpdump_text()` and `load_lpdump_report()` work.
- PASS: Parses metadata size/slots, block size, device size, and alignment.
- PASS: Parses group name, group maximum size, and flags.
- PASS: Parses partition name, group, size, readonly/attributes, and extent count.
- PASS: Supports A/B and non-A/B fixtures.
- PASS: Unknown partitions such as `vendor_boot` still parse; no RK3318/product_a/system_a hard-code.
- PASS: Empty or missing required fields raise `LpDumpParseError`.
- PASS: Does not call WSL, subprocess, `lpdump`, or any real ROM tool.
- PASS: Tests pass: `tests/test_lpdump_parser.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Real `lpdump` output may vary; add fixtures later if real ROM testing exposes another format.

### TASK-0207 — Implement `core/lpmake_builder.py`
Status: DONE

Scope:
- Build preview command for `lpmake` from parsed `SuperMetadata`.
- Do not call WSL, subprocess, `lpmake` or ROM tools.
- Do not modify GUI.

Acceptance:
- Added `LpMakeImageSource`, `LpMakeCommand` and `build_lpmake_command()`.
- Command preview includes metadata size, metadata slots, device size, block size, optional alignment, groups, partitions, images, sparse flag and output path.
- Values are built from parsed metadata and image source inputs, not hard-coded for one ROM.
- Missing image source raises `LpMakeBuildError` by default.
- Partition size override is supported.
- Group size validation raises `LpMakeBuildError` when effective partition sizes exceed maximum group size.
- Paths with spaces are shell-quoted safely in preview string.
- Unicode paths are preserved.
- `tests/test_lpmake_builder.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- `LpMakeCommand.args` keeps unquoted argv-style tokens; `command_string` is a safely quoted shell preview.
- Supports `sparse=True` and `sparse=False`.
- Uses parsed group and partition metadata from `SuperMetadata`.
- No WSL, subprocess, `lpmake`, GUI or ROM tool calls were added.
- Tests pass: `tests/test_lpmake_builder.py`, `compileall`, smoke test and full pytest.

Reviewer notes:
- PASS: Provides `LpMakeImageSource`, `LpMakeCommand`, and `build_lpmake_command()`.
- PASS: Command preview is built from `SuperMetadata`, without hard-coded size/name/group values.
- PASS: Includes metadata-size, metadata-slots, device-size, block-size, alignment, group, partition, image, sparse flag, and output path.
- PASS: Uses `parts/*.img` or `modified/*.img` according to `image_sources`.
- PASS: Missing image source raises `LpMakeBuildError`.
- PASS: Size override and group size validation work.
- PASS: Paths with spaces are quoted in `command_string`; Unicode paths are preserved.
- PASS: `sparse=True` includes `--sparse`; `sparse=False` omits `--sparse`.
- PASS: Does not call WSL, subprocess, `lpmake`, or any real ROM tool.
- PASS: Tests pass: `tests/test_lpmake_builder.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Real execution must verify the preview against the bundled `lpmake` binary.
- Non-blocker: Future `size_override` values must come from `resize_planner`/`ext4_image`, not manual input.

### TASK-0208 — Implement `core/partition_explorer.py`
Status: DONE

Scope:
- Build Partition Explorer core state for the Unpack tab.
- Combine detected images, sparse/raw status, optional AVB report summary and optional dynamic partition metadata.
- Reuse `core/image_detector.py`, `core/sparse_image.py`, `core/avb.py` and `core/lpdump_parser.py`.
- Do not call WSL, subprocess or real ROM tools.
- Do not modify GUI.

Acceptance:
- `build_partition_explorer(image_dir, vbmeta_report_path=None, lpdump_report_path=None, editable_root=None)` returns detected images, image groups, dynamic partitions, AVB summary, warnings and errors.
- `collect_detected_images(image_dir)` uses `image_detector` and returns `PartitionImageNode` entries.
- `load_optional_avb_summary(vbmeta_report_path)` parses text reports through `core/avb.py`.
- `load_optional_dynamic_partitions(lpdump_report_path, editable_root=None)` parses lpdump text reports through `core/lpdump_parser.py`.
- `super.img` is marked sparse/raw using `core/sparse_image.py` only; no `simg2img` execution.
- Empty `Image/` folder returns a valid result with warning.
- Missing `image_dir` raises `PartitionExplorerError`.
- AVB Hash/Hashtree descriptors add bootloop/AVB warning.
- Dynamic partitions preserve A/B, non-A/B and unknown partition names.
- Partition risk does not claim absolute safety.
- `tests/test_partition_explorer.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `PartitionExplorerResult`, `PartitionImageNode`, `DynamicPartitionNode`, `AvbSummary` and `PartitionExplorerError`.
- `build_partition_explorer()` combines data from existing core parsers and reports parse errors in the result.
- Dynamic partition actions are limited to `extract_tree` and `view_info`.
- No WSL, subprocess, GUI or ROM tool calls were added.
- Tests pass: `tests/test_partition_explorer.py`.

Reviewer notes:
- PASS: `core/partition_explorer.py` gathers detected images from `Image/`.
- PASS: Provides `PartitionExplorerResult`, `PartitionImageNode`, `DynamicPartitionNode`, `AvbSummary`, and `PartitionExplorerError`.
- PASS: Uses `image_detector` for scanning instead of duplicating image detection logic.
- PASS: Uses `sparse_image` to mark `super.img` sparse/raw without running `simg2img`.
- PASS: Uses `avb.py` to parse optional vbmeta text reports.
- PASS: Uses `lpdump_parser.py` to parse optional dynamic partition reports.
- PASS: Provides image groups: `super_images`, `vbmeta_images`, `boot_images`, and `danger_images`.
- PASS: Empty `Image/` folder returns a valid result with warning; missing `image_dir` raises `PartitionExplorerError`.
- PASS: AVB Hash/Hashtree descriptors create bootloop/AVB warnings.
- PASS: Dynamic partitions preserve A/B, non-A/B, and unknown partition names.
- PASS: Partition risk does not claim absolute safety.
- PASS: Does not call WSL, subprocess, `afptool`, `simg2img`, `lpdump`, `lpunpack`, `lpmake`, `avbtool`, or any real ROM tool.
- PASS: Does not modify GUI.
- PASS: Tests pass: `tests/test_partition_explorer.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Real workflow should pass source image roots explicitly instead of relying on `_infer_source_image_path()`.

### TASK-0209 — Improve `core/project_state.py` for detected images and partition explorer state
Status: DONE

Scope:
- Persist project and Partition Explorer state to JSON.
- Preserve ROM path, project name, project/work/image/editable/output/report dirs, detected images, dynamic partitions, AVB summary and partition flags.
- Do not hard-code workspace absolute paths.
- Do not call WSL, subprocess or real ROM tools.
- Do not modify GUI.

Acceptance:
- `create_project_state(...)` creates schema-versioned state.
- `save_project_state(state, path)` writes UTF-8 JSON without losing Unicode.
- `load_project_state(path)` loads state and raises `ProjectStateError` for missing/invalid files.
- `update_partition_explorer_state(state, explorer_result)` stores detected images, dynamic partitions and AVB summary.
- `mark_partition_extracted(state, partition_name, editable_dir)` records extracted partition state.
- `mark_partition_modified(state, partition_name)` records modified partition state.
- `get_partition_source_image(state, partition_name)` uses `modified/*.img` for modified partitions and `parts/*.img` otherwise.
- `tests/test_project_state.py` pass.
- `python -m compileall .` pass.
- `python app.py --smoke-test` pass.
- `python -m pytest` pass.

Implementation notes:
- Added `ProjectState`, `ProjectDetectedImage`, `ProjectDynamicPartition`, `ProjectAvbSummary` and `ProjectStateError`.
- JSON is written with `ensure_ascii=False` and UTF-8 encoding.
- Paths are persisted as strings and derived from the project dir passed by callers.
- State keeps `schema_version`, `created_at` and `updated_at`.
- No WSL, subprocess, GUI or ROM tool calls were added.
- Tests pass: `tests/test_project_state.py`.

Reviewer notes:
- PASS: `core/project_state.py` persists project state as UTF-8 JSON.
- PASS: Provides `ProjectState`, `ProjectDetectedImage`, `ProjectDynamicPartition`, `ProjectAvbSummary`, and `ProjectStateError`.
- PASS: Provides `create_project_state()`, `save_project_state()`, `load_project_state()`, `update_partition_explorer_state()`, `mark_partition_extracted()`, `mark_partition_modified()`, and `get_partition_source_image()`.
- PASS: Preserves Vietnamese Unicode in project names and paths.
- PASS: Keeps `schema_version`, `created_at`, and `updated_at`.
- PASS: Missing/invalid state files raise `ProjectStateError` clearly.
- PASS: Does not hard-code workspace absolute paths.
- PASS: Does not call WSL, subprocess, or any real ROM tool.
- PASS: Does not modify GUI.
- PASS: Tests pass: `tests/test_project_state.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Future project creation should standardize the real `image_dir` as `project_dir/work/update/Image` or pass it explicitly.
- Non-blocker: Real workflow should generate AVB/lpdump reports through `WslRunner` in a later task.

## Phase 3 — GUI core state wiring

### TASK-0301 — Wire Project tab to ProjectState
Status: DONE

Scope:
- Connect `gui/project_tab.py` to `core/project_state.py`, `core/app_paths.py`, and `core/tool_config.py`.
- Project tab creates project folder structure and saves `project_state.json`.
- Do not copy large ROM files.
- Do not allow manual workspace or tool path selection.
- Do not call WSL, subprocess, or real ROM tools.

Acceptance:
- User can select original `update.img`, enter project name, optionally select APK path, and create a project.
- Project dir is created under `APP_ROOT/workspace/projects/<project_name>`.
- Minimal subdirs are created: `work/`, `work/update/`, `work/update/Image/`, `work/reports/`, `work/parts/`, `work/modified/`, `editable/`, `output/`, `logs/`.
- `project_state.json` stores project name, ROM path, project dirs, selected APK path, timestamps and schema version.
- Existing project names are rejected clearly.
- Tools are displayed read-only from `APP_ROOT/tools` with OK/MISSING status.
- `tests/test_gui_project_state_flow.py` pass.

Implementation notes:
- Added `create_project_from_inputs()` and `ProjectCreationError` in `gui/project_tab.py` for testable project creation flow.
- `ProjectTab` emits `project_created(state, state_path)` and can load an existing `project_state.json`.
- Added `selected_apk_path` to `ProjectState` without breaking existing JSON load.
- No WSL, subprocess, GUI workspace picker, tool path picker, ROM copy, or real tool calls were added.

Reviewer notes:
- PASS: Project tab allows selecting original `update.img`, entering project name, and optionally selecting APK.
- PASS: Optional APK path is saved as `selected_apk_path` in project state.
- PASS: Project dir is created under `APP_ROOT/workspace/projects/<project_name>`.
- PASS: Creates required folders: `work/`, `work/update/`, `work/update/Image/`, `work/reports/`, `work/parts/`, `work/modified/`, `editable/`, `output/`, `logs/`.
- PASS: Saves `project_state.json` and does not copy large ROM files.
- PASS: Existing project names are rejected clearly.
- PASS: Workspace and tool paths cannot be selected manually.
- PASS: Bundled tools are shown read-only with OK/MISSING status.
- PASS: Does not call WSL, subprocess, or real ROM tools.
- PASS: Tests pass: `tests/test_gui_project_state_flow.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Later task should reject Windows reserved project names such as `CON`, `PRN`, `AUX`, and `NUL`.
- Non-blocker: `ProjectTab` should later catch `OSError`/`ProjectStateError` for nicer write/save permission errors.

### TASK-0302 — Wire Unpack tab to PartitionExplorer
Status: DONE

Scope:
- Connect `gui/unpack_tab.py` to `core/partition_explorer.py` and `core/project_state.py`.
- Refresh detected images/dynamic partitions from existing `Image/` and report text files.
- Keep action buttons disabled/log-only for real tool execution.
- Do not call WSL, subprocess, or real ROM tools.

Acceptance:
- Unpack tab reads current project state from MainWindow.
- Without a project, Unpack tab shows a clear warning and does not crash.
- Refresh calls `build_partition_explorer()` with `image_dir`, optional `work/reports/vbmeta_info.txt`, optional `work/reports/lpdump_original.txt`, and `editable_dir`.
- Detected images table displays name, type, size, risk, supported actions, status and notes.
- Dynamic partitions table displays name, group, size, readonly, editable dir, risk and supported actions.
- AVB summary displays algorithm, flags, risk, affected partitions and warnings.
- Refresh updates and saves `project_state.json`.
- Empty `Image/` folder is handled with warning.
- `tests/test_gui_unpack_partition_flow.py` pass.

Implementation notes:
- Added `refresh_partition_explorer_state()` and `UnpackFlowError` in `gui/unpack_tab.py`.
- `UnpackTab` emits `project_state_updated(state, state_path)` after refresh.
- Detected image and dynamic partition tables can now be populated from core state.
- No WSL, subprocess, unpack/repack, or real tool calls were added.

Reviewer notes:
- PASS: Unpack tab reads current project state from MainWindow.
- PASS: Missing project shows a clear warning and does not crash.
- PASS: Refresh calls `build_partition_explorer()` with `image_dir`, optional `vbmeta_info.txt`, optional `lpdump_original.txt`, and `editable_dir`.
- PASS: Detected images table is populated from core result.
- PASS: Dynamic partitions table is populated from core result.
- PASS: AVB summary is populated from core result.
- PASS: Refresh updates and saves `project_state.json`.
- PASS: Empty `Image/` folder does not crash and shows a clear warning.
- PASS: Real tool actions remain disabled/log-only.
- PASS: Does not call WSL, subprocess, or real ROM tools.
- PASS: Tests pass: `tests/test_gui_unpack_partition_flow.py`, `compileall`, smoke test, and full pytest.
- Non-blocker: Later task will create real `vbmeta_info.txt` and `lpdump_original.txt` through `WslRunner`.

### TASK-0303 — Add GUI state loading/saving flow
Status: DONE

Scope:
- Add simple GUI state holder flow between Project tab, MainWindow, and Unpack tab.
- Support manual load of `project_state.json`.
- Keep 7-tab sidebar unchanged.
- Do not introduce global state.

Acceptance:
- `MainWindow` holds `current_project_state` and `current_project_state_path`.
- Project creation/loading updates MainWindow state and passes it to Unpack tab.
- Unpack refresh persists state and informs MainWindow.
- Sidebar remains exactly 7 tabs in the locked order.
- No Setup tab and no separate Verify tab are added.
- `python -m compileall .`, smoke test and full pytest pass.

Implementation notes:
- `MainWindow` wires Project tab signals to Unpack tab via `_set_project_state()`.
- Status bar shows current project name after create/load.
- Existing mock UI for other tabs is unchanged.

Reviewer notes:
- PASS: `MainWindow` holds `current_project_state` and `current_project_state_path`.
- PASS: Project tab emits `project_created` and `project_loaded`.
- PASS: MainWindow receives project state and passes it to Unpack tab.
- PASS: Unpack tab emits `project_state_updated` after refresh.
- PASS: Sidebar remains exactly 7 tabs: Project, Unpack, Analyze, Edit ROM Folder, Apply Changes, Rebuild Super, Repack & Verify.
- PASS: No Setup tab and no separate Verify tab were added.
- PASS: Does not use uncontrolled global state.
- PASS: Tests pass: `compileall`, smoke test, full pytest, and offscreen GUI instantiate with 7 tabs.

## Phase 4 - Real unpack/analyze workflow foundation

### TASK-0401 - Implement RKFW/RKAF unpack workflow
Status: REVIEW

Scope:
- Add `core/rkaf.py` workflow foundation for unpacking RKFW then RKAF through the provided runner.
- Use bundled `tools/afptool-rs/afptool-rs` from `core/tool_config.py`.
- Convert Windows paths to WSL paths and quote shell paths safely.
- Do not repack ROM, apply diff, flash device, or call external commands outside `WslRunner`.

Acceptance:
- `unpack_rkfw_rkaf()` builds `afptool-rs unpack <update.img> <work/outer>`.
- It finds `embedded-update.img` or update-like output in `work/outer`.
- It builds `afptool-rs unpack <embedded-update.img> <work/update>`.
- Missing `afptool-rs` raises a clear workflow error before running any command.
- Missing embedded RKAF image raises a clear error and reports available files.
- Tests use fake runner and fake filesystem output only.
- `tests/test_rkaf.py` pass.

Implementation notes:
- Added `RkafWorkflowError` and `RkafUnpackResult`.
- Commands are recorded in `commands_run` for GUI/logging later.
- `core/tool_config.py` now checks the standard binary path `tools/afptool-rs/afptool-rs`.
- No GUI, ROM repack, WSL direct call, subprocess direct call, or real tool invocation was added.

### TASK-0402 - Implement super.img analyze workflow
Status: REVIEW

Scope:
- Add `core/super_image.py` workflow foundation for sparse/raw detection and lpdump report generation.
- Use `core/sparse_image.py` for sparse detection.
- Use bundled `simg2img` only when sparse and bundled `lpdump` for report generation.
- Parse generated `lpdump_original.txt` when present.

Acceptance:
- Sparse `super.img` builds `simg2img <super.img> <work/super/super.raw.img>`.
- Raw `super.img` skips `simg2img` and uses the original image path for `lpdump`.
- `lpdump <raw_super> > <work/reports/lpdump_original.txt>` command is built with quoted WSL paths.
- Missing `super.img`, `simg2img`, or `lpdump` raises clear errors.
- Tests use fake runner and generated text fixtures only.
- `tests/test_super_image.py` pass.

Implementation notes:
- Added `SuperImageWorkflowError` and `SuperAnalyzeResult`.
- `metadata_summary` is populated when the generated report can be parsed by `core/lpdump_parser.py`.
- `core/tool_config.py` now checks `tools/lptools/simg2img`.
- No GUI, lpunpack, lpmake, repack, direct WSL call, subprocess direct call, or real tool invocation was added.

### TASK-0403 - Generate vbmeta/lpdump reports for Partition Explorer
Status: REVIEW

Scope:
- Add `core/workflow.py` combined unpack/analyze foundation.
- Generate `work/reports/vbmeta_info.txt` using `avbtool.py info_image` command through runner.
- Generate `work/reports/lpdump_original.txt` through `core/super_image.py`.
- Refresh Partition Explorer state from generated reports.

Acceptance:
- `generate_vbmeta_report()` builds `python3 <avbtool.py> info_image --image <vbmeta.img> > <reports/vbmeta_info.txt>`.
- Missing `vbmeta.img` returns `None` without crashing.
- `run_unpack_and_analyze_workflow()` calls RKFW/RKAF unpack, optional vbmeta analyze, optional super analyze, then `build_partition_explorer()`.
- Project state is updated with detected images, dynamic partitions, and AVB summary; it is saved when `state_path` is provided.
- Missing tool raises clear `WorkflowError`.
- Tests use fake runner only and do not require WSL or bundled tools to exist.
- `tests/test_workflow_unpack_analyze.py` pass.

Implementation notes:
- Added `WorkflowError` and `RomAnalyzeWorkflowResult`.
- Workflow preserves warnings for missing `super.img`/`vbmeta.img` and parser warnings.
- No GUI, repack final, apply diff, resize, flash, direct WSL call, subprocess direct call, or real tool invocation was added.
