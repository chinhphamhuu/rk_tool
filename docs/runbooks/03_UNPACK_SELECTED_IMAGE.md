# 03_UNPACK_SELECTED_IMAGE

## Mục tiêu

Analyze hoặc unpack image được chọn trong Partition Explorer.

## `super.img`

1. Analyze sparse magic.
2. Nếu sparse thì chạy `simg2img`.
3. Chạy `lpdump` và lưu metadata gốc.
4. Chạy `lpunpack`.
5. Hiển thị dynamic partitions:
   - A/B: `system_a`, `product_a`, `vendor_a`, `odm_a`, `system_ext_a`
   - non-A/B: `system`, `product`, `vendor`, `odm`, `system_ext`
6. Khi người dùng chọn partition, extract tree ra:

```text
workspace/projects/<project>/editable/<partition_name>/
```

## `vbmeta.img`

- Analyze bằng `tools/avbtool/avbtool.py`.
- Không extract cây thư mục.
- Nếu có Hash descriptor hoặc Hashtree descriptor thì cảnh báo đỏ.

## `boot.img` / `recovery.img`

- MVP chỉ Analyze/Advanced.
- Không sửa boot/recovery trong MVP.

## `dtbo.img`

- Info only.

## `uboot.img` / `trust.img`

- Không sửa trong MVP.
- Cảnh báo nguy hiểm.

## `parameter.txt`

- Cho mở xem.
- Nếu sửa thì cảnh báo nguy hiểm.
