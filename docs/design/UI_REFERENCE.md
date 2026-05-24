# UI_REFERENCE

GUI mới bám theo 7 màn trong `docs/design/screenshots/`.

## Mapping ảnh reference

- `01_project.png` — Tab Project: tạo project, chọn ROM gốc, APK tùy chọn, workspace tự động, bundled tools read-only, LogPanel.
- `ChatGPT Image 16_59_28 24 thg 5, 2026 (8).png` — Tab Unpack: step card RKFW/RKAF/detect images và bảng images đã phát hiện.
- `ChatGPT Image 16_59_29 24 thg 5, 2026 (9).png` — Tab Unpack: Partition Explorer cho `super.img`, dynamic partitions và cây editable sẽ tạo ra.
- `ChatGPT Image 16_59_27 24 thg 5, 2026 (6).png` — Tab Analyze: RKFW Header, MD5 Tail, vbmeta/AVB, super layout, partition free space và cảnh báo kỹ thuật.
- `ChatGPT Image 16_59_26 24 thg 5, 2026 (5).png` — Tab Edit ROM Folder: cây editable, nội dung partition, scan changes và cảnh báo rủi ro.
- `ChatGPT Image 16_59_27 24 thg 5, 2026 (7).png` — Tab Apply Changes: diff table, resize plan, checklist apply và LogPanel.
- `ChatGPT Image 16_59_25 24 thg 5, 2026 (2).png` — Tab Rebuild Super: nguồn image partition, metadata từ lpdump, command preview và verify quick.
- `ChatGPT Image 16_59_26 24 thg 5, 2026 (4).png` — Tab Repack & Verify: checklist đóng gói/verify đang chạy, output info và warning verify offline.
- `ChatGPT Image 16_59_25 24 thg 5, 2026 (3).png` — Tab Repack & Verify: trạng thái `Verify offline PASS` và thông tin ROM final.

## Style cần giữ

- Nền sáng, card bo góc, spacing rộng rãi.
- Sidebar trái có icon, active state nền xanh nhạt.
- Button chính màu xanh.
- Badge OK xanh lá, warning vàng/cam, error đỏ.
- LogPanel realtime nằm dưới cùng mỗi tab.
- Không có Setup tab.
- Không có Verify tab riêng.
