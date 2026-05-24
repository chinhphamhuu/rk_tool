# 05_APPLY_DIFF

## Mục tiêu

Apply diff từ folder editable vào bản copy của image partition.

## Quy tắc

- Không repack trực tiếp từ folder editable.
- Không sửa image gốc trong `parts/`.
- Chỉ sửa image copy trong `modified/`.

## Luồng

1. Copy image gốc từ `parts/*.img` sang `modified/*.img`.
2. Tính dung lượng cần resize từ diff.
3. Resize bằng `truncate` và `resize2fs` nếu thiếu dung lượng.
4. Apply diff vào image bằng `debugfs`.
5. Set permission:
   - folder `0755`
   - file `0644`
   - APK `0644`
6. Set owner mặc định `root:root`.
7. Set SELinux mặc định `u:object_r:system_file:s0`.
8. Chạy `e2fsck -fy`.
9. Lưu trạng thái partition đã sửa vào `project_state`.
