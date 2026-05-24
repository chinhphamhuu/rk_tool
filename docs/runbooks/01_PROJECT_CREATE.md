# 01_PROJECT_CREATE

## Mục tiêu

Tạo project mới trong workspace tự động của app.

## Quy tắc

- Người dùng chọn ROM gốc `update.img`.
- Người dùng nhập tên project.
- Người dùng có thể chọn APK tùy chọn.
- Không cho chọn workspace thủ công.
- Không cho chọn tool path thủ công.
- GUI hiển thị workspace tự động và bundled tools ở trạng thái read-only.

## Đường dẫn

`APP_ROOT`:

- Chạy Python: thư mục chứa `app.py`.
- Chạy EXE: thư mục chứa file EXE.

Project được tạo tại:

```text
APP_ROOT/workspace/projects/<project_name>/
```

Workspace app gồm:

```text
APP_ROOT/workspace/projects/
APP_ROOT/workspace/output/
APP_ROOT/workspace/logs/
APP_ROOT/workspace/temp/
```
