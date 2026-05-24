# PRODUCT_SPEC — Rockchip Android ROM Repack GUI

## Mục tiêu

Tạo tool GUI Windows để người dùng phổ thông có thể unpack, chỉnh sửa, rebuild, repack và verify offline ROM Android box Rockchip.

## Phạm vi MVP

- Chip mục tiêu đầu tiên: RK3318.
- Android mục tiêu đầu tiên: Android 11.
- ROM dạng `update.img` Rockchip có RKFW/RKAF và `super.img` dynamic partitions.
- GUI PySide6, backend xử lý ROM qua WSL Ubuntu.
- Không flash thiết bị trong MVP.

## UX đã chốt

Không có tab Setup. Các tool được đóng gói trong `tools/`.

Không có tab Verify riêng. Verify chạy tự động trong `Repack & Verify`.

Sidebar:

1. Project
2. Unpack
3. Analyze
4. Edit ROM Folder
5. Apply Changes
6. Rebuild Super
7. Repack & Verify

## Workspace

App tự tạo workspace trong:

```text
APP_ROOT/workspace/
```

Cấu trúc:

```text
workspace/projects/<project_name>/
workspace/output/
workspace/logs/
workspace/temp/
```

Không cho người dùng chọn workspace thủ công.

`APP_ROOT` được xác định như sau:

- Nếu chạy bằng Python: thư mục chứa `app.py`.
- Nếu đóng gói EXE: thư mục chứa file EXE.

Mỗi project được tạo trong:

```text
APP_ROOT/workspace/projects/<project_name>/
```

## Tool bundled

Các tool nằm trong:

```text
tools/afptool-rs/
tools/lptools/lpunpack
tools/lptools/lpmake
tools/lptools/lpdump
tools/avbtool/avbtool.py
```

GUI không hiển thị màn chọn đường dẫn tool và không cho người dùng chọn tool path.

GUI không gọi subprocess trực tiếp. Mọi lệnh hệ thống/WSL phải đi qua `core/wsl_runner.py`.

## Luồng chính

1. Project: chọn ROM gốc, nhập tên project, chọn APK tùy chọn, hiển thị workspace tự động và bundled tools read-only.
2. Unpack: unpack RKFW, unpack RKAF, detect images.
3. Unpack theo image: `super.img`/`vbmeta.img`/`boot.img`...
4. Edit ROM Folder: chỉnh cây thư mục staging đã extract trong `editable/<partition>/`.
5. Apply Changes: scan diff, fix permission/SELinux, resize image nếu cần, apply bằng debugfs.
6. Rebuild Super: parse `lpdump`, tạo `lpmake`, rebuild `super.img`.
7. Repack & Verify: pack RKAF/RKFW, restore header, tính MD5 tail, verify offline.

## Partition Explorer

Sau khi unpack RKFW/RKAF, tab Unpack hiển thị:

- `super.img`: Dynamic partition container → Analyze / Unpack / Extract dynamic partitions.
- `vbmeta.img`: AVB metadata → Analyze AVB.
- `boot.img`: Boot image → Advanced trong MVP.
- `recovery.img`: Recovery image → Advanced trong MVP.
- `dtbo.img`: Info only.
- `uboot.img`: Không sửa trong MVP.
- `trust.img`: Không sửa trong MVP.
- `parameter.txt`: Text, cho mở xem/sửa có cảnh báo.

Với `super.img`:

1. Analyze sparse magic.
2. Nếu sparse thì chạy `simg2img`.
3. Chạy `lpdump` và lưu metadata gốc.
4. Chạy `lpunpack`.
5. Hiển thị dynamic partitions, ví dụ:
   - `system_a`
   - `product_a`
   - `vendor_a`
   - `odm_a`
   - `system_ext_a`
   - hoặc biến thể non-A/B: `system`, `product`, `vendor`, `odm`, `system_ext`

Người dùng chọn partition rồi extract tree ra:

```text
workspace/projects/<project>/editable/<partition_name>/
```

Với `vbmeta.img`, app chỉ analyze bằng `avbtool.py`. Nếu có Hash descriptor hoặc Hashtree descriptor thì cảnh báo đỏ. MVP không extract cây thư mục từ `vbmeta.img`.

Với `boot.img` và `recovery.img`, MVP chỉ Analyze/Advanced, không sửa boot/recovery.

Với `uboot.img` và `trust.img`, MVP không sửa và phải cảnh báo nguy hiểm.

## Edit ROM Folder

Folder editable chỉ là staging. App không repack trực tiếp từ folder editable.

Người dùng có thể mở folder bằng Explorer để sửa file. App phải có Scan changes, so sánh manifest before/after và hiển thị:

- `+` file mới
- `-` file xóa
- `M` file sửa

Kết quả scan cần cảnh báo xanh/vàng/đỏ theo mức rủi ro.

## Apply Changes

Khi Apply:

1. Copy image gốc từ `parts/*.img` sang `modified/*.img`.
2. Tính dung lượng cần resize.
3. Resize bằng `truncate` và `resize2fs` nếu thiếu dung lượng.
4. Apply diff vào image bằng `debugfs`.
5. Set permission mặc định:
   - folder `0755`
   - file `0644`
   - APK `0644`
6. Set owner mặc định `root:root`.
7. Set SELinux mặc định `u:object_r:system_file:s0`.
8. Chạy `e2fsck -fy`.
9. Lưu trạng thái partition đã sửa vào `project_state`.

## Rebuild Super

Khi rebuild `super.img`:

1. Dùng `modified/*.img` nếu partition đã sửa.
2. Dùng `parts/*.img` nếu partition không sửa.
3. Build command `lpmake` từ `lpdump` gốc.
4. Không hard-code `device-size`, `group-size`, `partition-name` cho một ROM cụ thể.
5. Verify super mới bằng `simg2img`, `lpdump` và `lpunpack` thử.

## Repack & Verify

Khi người dùng bấm repack, app tự chạy:

1. Pack RKAF.
2. Pack RKFW.
3. Restore RKFW header từ ROM gốc tại offset `0x15`.
4. Recalculate 32 byte ASCII MD5 tail cuối file RKFW.
5. Verify RKFW header.
6. Verify MD5 tail.
7. Unpack thử RKFW final.
8. Unpack thử RKAF final.
9. Verify `super.img`.
10. Check file/APK đã thêm còn tồn tại.
11. Ghi SHA256 final.

Kết quả chỉ được ghi: `Verify offline PASS`, không claim chắc chắn boot thành công.
