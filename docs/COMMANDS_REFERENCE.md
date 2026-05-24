# COMMANDS_REFERENCE

## Cài dependency WSL

```bash
sudo apt update
sudo apt install -y e2fsprogs android-sdk-libsparse-utils python3 file coreutils rsync
```

## Unpack RKFW

```bash
afptool-rs unpack update.img work/outer
```

## Unpack RKAF

```bash
afptool-rs unpack work/outer/embedded-update.img work/update
```

## Kiểm tra vbmeta

```bash
python3 tools/avbtool/avbtool.py info_image --image work/update/Image/vbmeta.img
```

## Convert super sparse sang raw

Kiểm tra sparse magic trước khi convert:

```bash
file work/update/Image/super.img
```

```bash
simg2img work/update/Image/super.img work/super/super.raw.img
```

## Dump layout dynamic partitions

```bash
lpdump work/super/super.raw.img > work/meta/lpdump_original.txt
```

## Unpack super

```bash
lpunpack work/super/super.raw.img work/parts
```

## Extract ext4 partition ra folder

```bash
sudo mount -o loop,ro work/parts/product_a.img work/mount/product_a
sudo rsync -aHAX --numeric-ids work/mount/product_a/ workspace/projects/demo/editable/product_a/
sudo umount work/mount/product_a
```

## Resize image

```bash
truncate -s 628748288 work/modified/product_a.img
resize2fs work/modified/product_a.img
```

## Apply diff bằng debugfs

Trước khi apply, copy image gốc từ `parts/` sang `modified/`:

```bash
cp work/parts/product_a.img work/modified/product_a.img
```

Ví dụ add APK và set metadata MVP:

```bash
cat > work/meta/debugfs_add_apk.cmds <<EOF
cd /app
mkdir DLTivi
cd DLTivi
write workspace/projects/demo/editable/product_a/app/DLTivi/DLTivi.apk DLTivi.apk
set_inode_field /app/DLTivi mode 040755
set_inode_field /app/DLTivi/DLTivi.apk mode 0100644
ea_set /app/DLTivi security.selinux u:object_r:system_file:s0
ea_set /app/DLTivi/DLTivi.apk security.selinux u:object_r:system_file:s0
EOF

debugfs -w -f work/meta/debugfs_add_apk.cmds work/modified/product_a.img
```

## e2fsck

```bash
e2fsck -fy work/modified/product_a.img
```

## Rebuild super bằng lpmake

Phải parse từ `lpdump` gốc, không hard-code cho mọi ROM.
Partition đã sửa dùng image từ `modified/`; partition không sửa dùng image từ `parts/`.

```bash
lpmake \
  --metadata-size 65536 \
  --metadata-slots 2 \
  --device-size 3607101440 \
  --block-size 4096 \
  --alignment 1048576 \
  --group rockchip_dynamic_partitions:3602907136 \
  --partition product_a:readonly:628748288:rockchip_dynamic_partitions \
  --image product_a=work/modified/product_a.img \
  --sparse \
  --output work/modified/super.img
```

## Verify super mới

```bash
simg2img work/modified/super.img work/verify/super.raw.img
lpdump work/verify/super.raw.img > work/verify/lpdump_rebuilt.txt
lpunpack work/verify/super.raw.img work/verify/parts
```

## Pack RKAF

```bash
afptool-rs pack-rkaf work/modified/update work/modified/embedded-update-new.img --model 'H96_Max_RK3318' --manufacturer 'Rockchip'
```

## Pack RKFW

```bash
afptool-rs pack-rkfw work/modified/outer work/modified/update_tmp.img --chip RK3308 --version 11.0.0 --timestamp 1679920630 --code 0x01060005
```

## Fix header + MD5 tail

```bash
python3 scripts/fix_rkfw_header_md5.py original.img update_tmp.img update_final.img
```

## Verify final

```bash
python3 scripts/verify_rkfw_image.py update_final.img
afptool-rs unpack update_final.img work/verify_final/outer
```
