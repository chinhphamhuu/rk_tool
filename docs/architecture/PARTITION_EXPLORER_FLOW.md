# PARTITION_EXPLORER_FLOW

## Sau khi unpack RKAF

App scan `work/update/Image/` và detect:

- `super.img`
- `vbmeta.img`
- `boot.img`
- `recovery.img`
- `dtbo.img`
- `uboot.img`
- `trust.img`
- `misc.img`
- `parameter.txt`

## Hành động theo loại image

- `super.img`: Analyze / Unpack → `simg2img`, `lpdump`, `lpunpack`, hiện dynamic partitions.
- `vbmeta.img`: Analyze AVB bằng `avbtool.py`.
- `boot.img`, `recovery.img`: Advanced, MVP chưa sửa.
- `dtbo.img`: Info only.
- `uboot.img`, `trust.img`: Không sửa.
- `parameter.txt`: Mở text, cảnh báo nguy hiểm.
