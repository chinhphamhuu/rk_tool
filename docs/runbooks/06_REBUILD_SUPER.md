# 06_REBUILD_SUPER

## Mục tiêu

Rebuild `super.img` từ dynamic partition images và metadata gốc.

## Input

- `lpdump` gốc đã lưu khi unpack `super.img`.
- `parts/*.img` cho partition không sửa.
- `modified/*.img` cho partition đã sửa.

## Quy tắc

- Dùng `modified/*.img` nếu partition đã sửa.
- Dùng `parts/*.img` nếu partition không sửa.
- Command `lpmake` phải build từ `lpdump` gốc.
- Không hard-code `device-size`, `group-size`, `partition-name`.

## Verify sau rebuild

1. Nếu output sparse thì convert thử bằng `simg2img`.
2. Chạy `lpdump` trên super mới.
3. Chạy `lpunpack` thử.
4. Báo lỗi nếu metadata hoặc unpack thử thất bại.
