# AGENTS

## Architect

Khóa kiến trúc, scope MVP, quyết định luồng an toàn.

## Implementer

Code theo task nhỏ. Không tự ý thêm flash, không tự ý đổi kiến trúc.

## Reviewer

Checklist bắt buộc:

- Sidebar còn đúng 7 tab không?
- Còn Setup/Verify riêng không?
- GUI có gọi subprocess trực tiếp không?
- Tool paths có còn bắt người dùng chọn không?
- Workspace có tự động trong `APP_ROOT/workspace` không?
- `super.img` flow có parse `lpdump` không?
- Có hard-code `lpmake` cho mọi ROM không?
- `Repack & Verify` có restore header + MD5 tail không?
- Docs/PROJECT_STATE/CHANGELOG đã cập nhật chưa?

## Tester

Chạy:

```bash
python -m compileall .
python -m pytest
python app.py --smoke-test
```
