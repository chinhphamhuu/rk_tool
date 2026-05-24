# TECHNICAL_KNOWLEDGE_BASE

## Cấu trúc ROM Rockchip Android 11

```text
update.img
└── RKFW wrapper
    ├── BOOT
    └── embedded-update.img
        └── RKAF package
            └── Image/
                ├── super.img
                ├── vbmeta.img
                ├── boot.img
                ├── recovery.img
                ├── dtbo.img
                ├── uboot.img
                └── ...
```

## Android 10/11/12

Android đời cao thường dùng:

- `super.img`
- dynamic partitions
- `system_a`, `product_a`, `vendor_a`, `odm_a`, `system_ext_a` hoặc bản không A/B
- `vbmeta` / AVB / dm-verity
- SELinux context
- Linux permission/owner/xattr/symlink

## Lỗi thường gặp khi chỉ unpack/repack

- Sai metadata `super.img`.
- Sai partition name, ví dụ đổi `product_a` thành `product`.
- Sai group size/device size/metadata size trong `lpmake`.
- Sai sparse/raw format.
- AVB/vbmeta còn descriptor nhưng không xử lý.
- Mất permission/SELinux/xattr/symlink.
- RKFW header bị đổi từ `H223` sang `H033`.
- MD5 tail cuối file RKFW sai.

## RKFW header + MD5 tail

- Header chip nằm tại offset `0x15`, dài 4 byte.
- ROM RK3318 Android 11 trong case mẫu dùng `H223`.
- `afptool-rs pack-rkfw` có thể tạo `H033`.
- RKFW có 32 byte ASCII MD5 ở cuối file.
- Sau khi sửa header hoặc payload, phải tính lại MD5 của toàn bộ file trừ 32 byte cuối, rồi ghi MD5 ASCII mới vào 32 byte cuối.

## Folder ROM editable

Folder editable chỉ là staging. Không coi folder này là source cuối tuyệt đối. Cách an toàn MVP:

1. Giữ image gốc.
2. Extract ra folder editable cho người dùng sửa.
3. Scan diff before/after.
4. Apply diff vào image copy bằng `debugfs`.
5. Resize nếu cần.
6. `e2fsck`.

Đường dẫn staging chuẩn:

```text
workspace/projects/<project>/editable/<partition_name>/
```

Đường dẫn image chuẩn:

```text
workspace/projects/<project>/parts/<partition_name>.img
workspace/projects/<project>/modified/<partition_name>.img
```

Khi Apply Changes, app copy image gốc từ `parts/` sang `modified/`, rồi chỉ apply diff vào bản copy. Không repack trực tiếp từ folder editable.

Permission/metadata mặc định trong MVP:

- folder: `0755`
- file: `0644`
- APK: `0644`
- owner: `root:root`
- SELinux: `u:object_r:system_file:s0`

## Dynamic partitions và lpmake

`super.img` phải được rebuild từ metadata gốc do `lpdump` cung cấp.

Không được hard-code:

- `device-size`
- `group-size`
- `metadata-size`
- `metadata-slots`
- `partition-name`
- A/B hoặc non-A/B suffix

Partition không sửa dùng image từ `parts/`. Partition đã sửa dùng image từ `modified/`.

## AVB/vbmeta

`vbmeta.img` chỉ analyze trong MVP. Nếu `avbtool.py info_image` cho thấy Hash descriptor hoặc Hashtree descriptor, GUI phải cảnh báo đỏ vì dm-verity/AVB có thể chặn ROM đã chỉnh sửa.
