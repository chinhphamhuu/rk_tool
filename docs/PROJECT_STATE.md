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

`TASK-0001` đã review PASS và DONE. `TASK-0101` đã review PASS và DONE. `TASK-0101B` đã review PASS và DONE. `TASK-0102` đã review PASS và DONE. `TASK-0103` đã review PASS và DONE. `TASK-0104` đã review PASS và DONE. `TASK-0200` đã review PASS và DONE. `TASK-0203` đã review PASS và DONE. `TASK-0204` đã review PASS và DONE. `TASK-0205`, `TASK-0206` và `TASK-0207` đã review PASS và DONE. `TASK-0208` và `TASK-0209` đã implement xong và đang ở REVIEW.

## Review mới nhất

`TASK-0205/0206/0207 — super.img metadata foundation`:

- PASS: `sparse_image.py` detect sparse magic đúng, chỉ đọc 4 byte header và lỗi missing/tiny rõ ràng.
- PASS: `lpdump_parser.py` parse metadata, groups, partitions cho A/B và non-A/B fixtures.
- PASS: Partition lạ như `vendor_boot` vẫn parse được; không hard-code RK3318/product_a/system_a.
- PASS: `lpmake_builder.py` build preview từ `SuperMetadata`, có group-size validation, missing source error, size override, sparse flag và quote path.
- PASS: Không gọi WSL, subprocess, `simg2img`, `lpdump`, `lpunpack`, `lpmake` hoặc ROM tool thật.
- PASS: Tests pass: `test_sparse_image.py`, `test_lpdump_parser.py`, `test_lpmake_builder.py`, `compileall`, smoke test và full pytest.
- Non-blocker: `lpdump` thực tế có thể khác fixture; khi test ROM thật nếu parse fail thì bổ sung fixture.
- Non-blocker: `lpmake` command khi chạy thật cần verify với binary `lpmake` thực tế.
- Non-blocker: `size_override` sau này phải lấy từ `resize_planner`/`ext4_image`, không nhập tay.

`TASK-0204 — Implement core/avb.py AVB/vbmeta info parser`:

- PASS: `core/avb.py` chỉ parse text report từ `avbtool info_image` output.
- PASS: Không gọi WSL, subprocess, `avbtool.py` thật, không đọc binary `vbmeta.img` thật và không sửa GUI.
- PASS: Có `AvbInfo`, `AvbDescriptor`, `AvbParseError`.
- PASS: Có `parse_avb_info_text(text)`, `load_avb_info_report(path)` và `classify_avb_risk(info)`.
- PASS: Parse được `Algorithm`, `Flags`, `Rollback Index`, Hash descriptor và Hashtree descriptor.
- PASS: Parse được descriptor metadata: `Partition Name`, `Image Size`, `Salt`, `Digest`/`Root Digest`.
- PASS: Detect Hash/Hashtree descriptors; `affected_partitions` không duplicate và không hard-code chỉ `system/product/vendor`.
- PASS: No-descriptor vbmeta với `Algorithm: NONE` + `Flags: 2` classify risk `low`; Hash/Hashtree descriptor classify risk `danger`.
- PASS: Empty/unrecognized text raise `AvbParseError` rõ ràng.
- PASS: Tests pass: `tests/test_avb.py`, `compileall`, smoke test và full pytest.
- Non-blocker: Workflow chạy `avbtool.py` thật phải làm ở task sau và đi qua `WslRunner`.
- Non-blocker: GUI Analyze tab sau này phải hiện cảnh báo đỏ nếu có Hash/Hashtree descriptor.
- Non-blocker: Không được kết luận chắc chắn AVB đã tắt, chỉ dùng wording `likely disabled` / `requires attention`.

`TASK-0203 — Image detector core`:

- PASS: `core/image_detector.py` chỉ scan filesystem bằng Python thuần.
- PASS: Không gọi WSL, subprocess, ROM tool thật và không sửa GUI.
- PASS: Detect đúng `super.img`, `vbmeta.img`, `boot.img`, `recovery.img`, `dtbo.img`, `uboot.img`, `trust.img`, `misc.img`, `parameter.txt` và unknown `.img`.
- PASS: `uboot.img`/`trust.img` là `bootloader_danger`, risk `danger`, action `info_only`.
- PASS: Empty `Image/` folder trả list rỗng; missing/non-directory path raise `ImageDetectorError` rõ ràng.
- PASS: Metadata trả về đủ `name`, `path`, `size_bytes`, `type`, `risk_level`, `supported_actions`.
- PASS: Tests pass: `tests/test_image_detector.py`, `compileall`, smoke test và full pytest.
- Non-blocker: `super.img` risk `safe` chấp nhận được cho analyze/unpack; khi làm rebuild super/lpmake thật cần thêm cảnh báo riêng vì sửa `super.img` vẫn có rủi ro.

`TASK-0104 — Implement core/rkfw.py RKFW header and MD5 tail utilities`:

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

`TASK-0001 — Update repo structure after UX change`:

- PASS: Docs phản ánh đúng 7 tab và đúng UX đã khóa.
- PASS: Không có Setup tab và không có Verify tab riêng trong spec/flow.
- PASS: Có Partition Explorer flow và runbook unpack selected image.
- PASS: Repack & Verify gộp verify offline, không claim ROM chắc chắn boot.
- PASS: Workspace tự động, bundled tools, editable staging, Apply diff/debugfs, Rebuild Super từ `lpdump` và Repack & Verify đã có trong docs.
- PASS: MVP không flash thiết bị.

`TASK-0103 — Implement core/path_utils.py`:

- PASS: Path conversion portable, không hard-code C:/D:, username, workspace hoặc tên máy.
- PASS: Hỗ trợ mọi drive letter Windows qua `/mnt/<drive>/...`; test có C, D và E.
- PASS: Không làm mất Unicode tiếng Việt và convert đúng path có dấu cách.
- PASS: `shell_quote()` quote an toàn bằng POSIX shell quoting.
- PASS: WSL UNC path được detect/convert; UNC network path raise lỗi MVP rõ ràng.
- PASS: Relative/invalid path raise `PathConversionError`.
- PASS: Không gọi WSL, subprocess, GUI hoặc ROM tool thật.
- PASS: Tests pass: `tests/test_path_utils.py`, `compileall`, smoke test và full pytest.

`TASK-0101 — Implement core/app_paths.py`:

- PASS: Detect `APP_ROOT` cho Python mode và frozen EXE mode.
- PASS: Workspace tự động nằm trong `APP_ROOT/workspace`.
- PASS: Tạo đủ `workspace/projects`, `workspace/output`, `workspace/logs`, `workspace/temp`.
- PASS: Không gọi WSL/subprocess và không cho người dùng chọn workspace thủ công.
- PASS: Tests pass: `tests/test_app_paths.py`.

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

`TASK-0208/0209 — Partition Explorer state foundation`:

- `core/partition_explorer.py` gom detected images từ `Image/`, sparse/raw status cho `super.img`, AVB summary từ report text nếu có, và dynamic partitions từ lpdump report text nếu có.
- `PartitionExplorerResult` có image groups cho `super.img`, `vbmeta.img`, boot/recovery, danger images, dynamic partition list, warnings và errors.
- AVB Hash/Hashtree descriptor được đưa vào warning để GUI Unpack/Analyze sau này hiển thị cảnh báo đỏ.
- Dynamic partitions giữ nguyên tên A/B, non-A/B hoặc partition lạ; không hard-code RK3318/product_a/system_a.
- `core/project_state.py` lưu project state JSON UTF-8 gồm ROM gốc, project dirs, detected images, dynamic partitions, AVB summary, extracted/modified partition flags và schema version.
- `get_partition_source_image()` chọn `modified/*.img` nếu partition đã modified, còn lại dùng `parts/*.img`.
- Chưa gọi WSL, subprocess, `afptool-rs`, `simg2img`, `lpdump`, `lpunpack`, `avbtool`, `lpmake` hoặc ROM tool thật.
- Dữ liệu này là nền tảng để GUI Unpack tab chuyển từ mock sang state core ở task sau.
- Tests pass: `tests/test_partition_explorer.py` và `tests/test_project_state.py`.

`TASK-0205/0206/0207 — super.img metadata foundation`:

- `core/sparse_image.py` detect Android sparse magic `3A FF 26 ED` bằng Python file I/O, chỉ đọc 4 byte header.
- `core/lpdump_parser.py` parse lpdump text thành `SuperMetadata`, `DynamicGroup`, `DynamicPartition`.
- Parser hỗ trợ A/B (`system_a`, `product_a`, `vendor_a`, `odm_a`, `system_ext_a`) và non-A/B (`system`, `product`, `vendor`, `odm`, `system_ext`) qua fixtures.
- Partition lạ như `vendor_boot` vẫn được parse, không hard-code chỉ RK3318 hoặc chỉ `product_a/system_a`.
- `core/lpmake_builder.py` build preview command từ metadata đã parse, gồm group/partition/image/output/sparse args.
- `LpMakeImageSource` hỗ trợ override partition size khi image đã resize.
- Có validate tổng size partition trong group không vượt `maximum_size`.
- Path có dấu cách được quote trong preview string; Unicode tiếng Việt được giữ nguyên.
- Chưa gọi `simg2img`, `lpdump`, `lpunpack`, `lpmake`, WSL, subprocess hoặc ROM tool thật.
- `lpmake` sau này phải chạy qua `core/wsl_runner.py`.
- Tests pass: `tests/test_sparse_image.py`, `tests/test_lpdump_parser.py`, `tests/test_lpmake_builder.py`, `compileall`, smoke test và full pytest.

`TASK-0204 — Implement core/avb.py AVB/vbmeta info parser`:

- `core/avb.py` parse text report từ output dạng `info_image --image vbmeta.img`.
- Added `AvbInfo`, `AvbDescriptor`, `AvbParseError`, `parse_avb_info_text()`, `load_avb_info_report()` và `classify_avb_risk()`.
- Parse `Algorithm`, `Flags`, `Rollback Index`, Hash descriptor và Hashtree descriptor.
- Detect `has_hash_descriptor`, `has_hashtree_descriptor`, `affected_partitions`, `is_disable_verification_likely`, `risk_level` và `warnings`.
- Có warning rõ khi ROM có AVB descriptors: sửa partition liên quan có thể bootloop nếu AVB không được xử lý đúng.
- Không hard-code chỉ `system/product/vendor`; descriptor partition bất kỳ như `odm`, `system_ext`, `vendor_boot` vẫn được đưa vào `affected_partitions`.
- Không gọi WSL, subprocess, `avbtool.py`, ROM tool thật hoặc GUI.
- Tests pass: `tests/test_avb.py`, `compileall`, smoke test và full pytest.

`TASK-0203 — Image detector core`:

- `core/image_detector.py` scan thư mục RKAF `Image/` bằng Python filesystem APIs.
- Detect `super.img`, `vbmeta.img`, `boot.img`, `recovery.img`, `dtbo.img`, `uboot.img`, `trust.img`, `misc.img`, `parameter.txt` và unknown `.img`.
- Trả metadata `name`, `path`, `size_bytes`, `type`, `risk_level`, `supported_actions`.
- `uboot.img`/`trust.img` được đánh dấu `bootloader_danger`, risk `danger`, action `info_only`.
- Empty `Image/` folder trả list rỗng; missing/non-directory path raise `ImageDetectorError`.
- Không gọi WSL, subprocess, ROM tool thật hoặc GUI.
- Tests pass: `tests/test_image_detector.py`, `compileall`, smoke test và full pytest.

`TASK-0104 — Implement core/rkfw.py RKFW header and MD5 tail utilities`:

- `read_rkfw_header()` đọc 4 byte header tại offset `0x15`.
- `copy_rkfw_header()` copy header từ ROM gốc sang image repacked/target.
- `read_md5_tail()`, `compute_body_md5()`, `verify_md5_tail()` và `rewrite_md5_tail()` xử lý MD5 tail 32 byte ASCII cuối file.
- `fix_header_and_md5_tail()` copy repacked sang output, restore header gốc, tính lại MD5 tail và trả `RkfwFixResult`.
- MD5 body đọc theo chunk, không load toàn bộ file vào RAM.
- File quá nhỏ raise `RkfwImageError` rõ ràng.
- Không gọi WSL, subprocess, `afptool-rs`, ROM tool thật hoặc GUI.
- Tests pass: `tests/test_rkfw_md5.py`, `compileall`, smoke test và full pytest.

`TASK-0103 — Implement core/path_utils.py`:

- `WindowsPathToWsl` convert path Windows dạng drive-letter sang WSL path dưới `/mnt/<drive>/`.
- Hỗ trợ path ổ C/D, path có dấu cách và Unicode tiếng Việt mà không normalize mất ký tự.
- Hỗ trợ WSL UNC path dạng `\\wsl$\Ubuntu-24.04\home\user\project` sang `/home/user/project`.
- UNC network path như `\\NAS\share\file.img` hoặc `\\192.168.1.10\share\file.img` raise lỗi rõ: chưa hỗ trợ trong MVP, hãy copy file vào workspace local.
- `shell_quote()` dùng POSIX shell quoting an toàn.
- Invalid path raise `PathConversionError` rõ ràng.
- Không gọi WSL, subprocess hoặc ROM tool thật.
- Tests pass: `tests/test_path_utils.py`, `compileall`, smoke test và full pytest.

`TASK-0101 — Implement core/app_paths.py`:

- `AppPaths.detect()` xác định `APP_ROOT`, `tools_dir`, `workspace_dir` và các thư mục con workspace.
- `_detect_app_root()` hỗ trợ Python mode và frozen EXE mode.
- `ensure_workspace()` tạo workspace tự động.
- Không gọi WSL/subprocess.

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

1. Review `TASK-0208/0209 — Partition Explorer state foundation` theo checklist.
2. Nếu review PASS, chuyển `TASK-0208` và `TASK-0209` sang DONE.
3. Implement backend wiring cho Project/Unpack sau khi core foundation tiếp tục ổn định.
