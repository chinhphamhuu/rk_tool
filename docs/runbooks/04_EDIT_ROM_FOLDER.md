# 04_EDIT_ROM_FOLDER

## Mục tiêu

Cho người dùng chỉnh folder ROM đã extract theo từng dynamic partition.

## Đường dẫn

Folder editable chuẩn:

```text
workspace/projects/<project>/editable/<partition_name>/
```

Ví dụ:

```text
workspace/projects/demo/editable/product_a/
workspace/projects/demo/editable/system_a/
```

## Quy tắc

- Folder editable chỉ là staging.
- Không repack trực tiếp từ folder editable.
- Người dùng có thể mở folder bằng Explorer.
- App phải có Scan changes.

## Scan changes

Scan changes so sánh manifest before/after và hiển thị:

- `+` file mới
- `-` file xóa
- `M` file sửa

Kết quả scan phải có cảnh báo xanh/vàng/đỏ theo mức rủi ro.
