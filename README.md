# Bot Golike - Tự động làm job

Bot tự động làm job trên Golike với 2 chế độ:
- **ADB Mode**: Điều khiển LDPlayer qua ADB (không chiếm chuột máy tính) ⭐ Khuyến nghị
- **Pyautogui Mode**: Điều khiển trực tiếp trên màn hình

## 🚀 Quick Start

### 1. Cài đặt
```bash
pip install -r requirements.txt
```

### 2. Cấu hình ADB
1. Bật ADB trong LDPlayer: **Cài đặt → Khác → ADB Debug (ON)**
2. Tìm package name Golike:
```bash
python find_golike_package.py
```
3. Chạy GUI và kết nối ADB:
```bash
python main.py
```

### 3. Upload Templates & Chạy
- Upload templates trong tab "📁 Templates"
- Click "▶️ Bắt đầu" trong tab "🎮 Điều khiển"

## ✨ Tính năng

- ✅ Tự động tìm và click job
- ✅ Tự động làm job Facebook (like, follow, share, comment)
- ✅ Tự động click "Hoàn thành" và xử lý OK/Fail
- ✅ Thống kê xu tự động (OCR)
- ✅ **Mở app Golike bằng package name** (không cần tìm icon)
- ✅ Hỗ trợ nhiều ADB devices
- ✅ Không chiếm chuột khi dùng ADB mode

## 📚 Tài liệu

- **`HUONG_DAN_TONG_HOP.md`** - Hướng dẫn đầy đủ (cấu hình, troubleshooting, tips)
- **`CHANGELOG.md`** - Lịch sử cập nhật
- **`START_HERE.md`** - Hướng dẫn bắt đầu nhanh

## 🔧 Scripts hữu ích

```bash
# Tìm package name Golike
python find_golike_package.py

# Test ADB
python test_adb_tap.py
python test_adb_keys.py
python test_adb_full_flow.py

# Test OCR xu
python test_coin_tracker.py
```

## 📊 ADB Mode vs Pyautogui Mode

| Tính năng | ADB Mode | Pyautogui Mode |
|-----------|----------|----------------|
| Chiếm chuột | ❌ Không | ✅ Có |
| Tốc độ | ⚡ Nhanh | 🐌 Chậm hơn |
| Mở app Golike | 📱 Package name | 🔍 Tìm icon |
| Cài đặt | 🔧 Cần ADB | ✅ Không cần |

## 🆕 Cập nhật mới (v2.1.0)

- ✅ Mở app Golike bằng package name (không cần tìm icon)
- ✅ OCR xu khi tìm thấy nút OK (chính xác hơn)
- ✅ Tổng hợp tài liệu thành 1 file

## 📁 Cấu trúc

```
.
├── main.py                    # Entry point
├── gui.py                     # Giao diện
├── sequence_worker.py         # Logic chính
├── ok_watcher.py             # Thread tự động click OK & OCR xu
├── adb_utils.py              # ADB controller (click, open app)
├── navigation.py             # Back actions, mở app Golike
├── coin_tracker.py           # Thống kê xu
├── find_golike_package.py    # Tìm package name Golike
├── templates/                # Templates
├── settings.json             # Cấu hình
└── HUONG_DAN_TONG_HOP.md    # Hướng dẫn đầy đủ
```

## 💡 Tips

- Dùng ADB mode để không bị chiếm chuột
- Tìm đúng package name Golike bằng `find_golike_package.py`
- Cài pytesseract hoặc easyocr để đọc xu tự động
- Xem log trong GUI để debug

## 📞 Hỗ trợ

Xem `HUONG_DAN_TONG_HOP.md` để biết chi tiết về troubleshooting và cấu hình nâng cao.

---

**Phiên bản:** 2.1.0  
**Cập nhật:** 2024-12-04
