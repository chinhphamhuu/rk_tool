# Rockchip Android ROM Repack GUI

Tool GUI Windows dùng để unpack, chỉnh sửa, rebuild và repack ROM Android box Rockchip.

## Scope MVP đã chốt

- GUI: Python 3.11+ + PySide6.
- Backend xử lý ROM: WSL Ubuntu qua `wsl.exe`.
- Tool đi kèm trong thư mục `tools/`, không hỏi người dùng chọn đường dẫn tool.
- Workspace tự động nằm trong `APP_ROOT/workspace/`, không hỏi người dùng chọn workspace.
- Không flash thiết bị trong MVP.
- Không có tab Setup.
- Không có tab Verify riêng.
- Verify được chạy tự động trong tab `Repack & Verify`.

## Sidebar mới

1. Project
2. Unpack
3. Analyze
4. Edit ROM Folder
5. Apply Changes
6. Rebuild Super
7. Repack & Verify

## Chạy app

```bash
pip install -r requirements.txt
python app.py
```

Smoke test:

```bash
python app.py --smoke-test
python -m compileall .
python -m pytest
```
