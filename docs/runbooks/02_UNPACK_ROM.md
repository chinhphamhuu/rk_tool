# 02_UNPACK_ROM

## Mục tiêu

Unpack ROM Rockchip `update.img` thành package RKAF và detect image trong `Image/`.

## Luồng

1. Unpack RKFW từ ROM gốc.
2. Unpack RKAF từ embedded update image.
3. Scan `update/Image/`.
4. Detect tối thiểu:
   - `super.img`
   - `vbmeta.img`
   - `boot.img`
   - `recovery.img`
   - `dtbo.img`
   - `uboot.img`
   - `trust.img`
   - `misc.img`
   - `parameter.txt`
   - file khác nếu có

## Quy tắc backend

GUI không gọi subprocess trực tiếp. Mọi lệnh unpack chạy qua service core và `core/wsl_runner.py`.
