# 07_REPACK_AND_VERIFY

## Mục tiêu

Repack ROM final và chạy verify offline tự động.

## Luồng bắt buộc

1. Pack RKAF.
2. Pack RKFW.
3. Restore RKFW header từ ROM gốc tại offset `0x15`.
4. Tính lại MD5 tail 32 byte ASCII cuối file RKFW.
5. Verify RKFW header.
6. Verify MD5 tail.
7. Unpack thử RKFW final.
8. Unpack thử RKAF final.
9. Verify `super.img` final.
10. Kiểm tra file/APK đã thêm còn tồn tại.
11. Ghi SHA256 final.

## Kết quả được phép báo

```text
Verify offline PASS.
ROM final sẵn sàng để thử flash bằng RKDevTool.
```

Không được claim ROM chắc chắn boot thành công.
