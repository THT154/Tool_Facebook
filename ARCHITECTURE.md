# 🏗️ Kiến trúc hệ thống Golike Bot (MVC Pattern)

> **Cập nhật**: Hệ thống đã được refactor theo mô hình MVC để dễ bảo trì và mở rộng.

## 📁 Cấu trúc thư mục (MVC Pattern)

```
Tool_facebook_vip/
├── main.py                 # Entry point
├── gui.py                  # Giao diện chính (View)
├── settings.json           # Cấu hình người dùng
├── requirements.txt        # Dependencies
├── ARCHITECTURE.md         # Documentation
│
├── Controllers/            # Business Logic Layer
│   ├── sequence_worker.py  # Controller chính - Điều phối jobs
│   ├── account_switcher.py # Controller tài khoản - Chuyển đổi account
│   ├── ok_watcher.py       # Controller popup - Xử lý popup
│   ├── job_detector.py     # Controller job - Phát hiện jobs
│   └── reset_navigation.py # Controller navigation - Reset điều hướng
│
├── Models/                 # Data Layer
│   ├── config.py           # Cấu hình hệ thống
│   ├── coin_tracker.py     # Model xu - Theo dõi xu
│   ├── blocked_accounts.txt      # Tài khoản bị block (vĩnh viễn)
│   ├── max_job_accounts.txt      # Tài khoản max job (reset mỗi ngày)
│   └── last_reset_date.txt       # Ngày reset cuối cùng
│
├── Utils/                  # Helper Layer
│   ├── adb_utils.py        # ADB helper - Điều khiển LDPlayer
│   ├── window_utils.py     # Window helper - Xử lý cửa sổ
│   ├── image_utils.py      # Image helper - Xử lý ảnh
│   ├── ocr_utils.py        # OCR helper - Đọc text
│   ├── navigation.py       # Navigation helper - Điều hướng
│   └── ldplayer_manager.py # LDPlayer helper - Quản lý LDPlayer
│
└── templates/              # Template images
    ├── job_icon.png
    ├── ok_button.png
    ├── account_selector.png
    └── ...
```

### Import Paths (Sau khi refactor)
```python
# Controllers
from Controllers.sequence_worker import SequenceWorker
from Controllers.account_switcher import AccountSwitcher
from Controllers.ok_watcher import OkWatcher
from Controllers.job_detector import JobDetector
from Controllers.reset_navigation import ResetNavigation

# Models
from Models.config import load_settings, save_settings
from Models.coin_tracker import get_coin_tracker

# Utils
from Utils.adb_utils import ADBController
from Utils.window_utils import click_at, get_ldplayer_window
from Utils.image_utils import load_gray, locate_template
from Utils.ocr_utils import extract_text_from_image
from Utils.navigation import press_back_method
from Utils.ldplayer_manager import LDPlayerManager
```

## 🔄 Luồng hoạt động

### 1. Khởi động
```
main.py
  └─> gui.py (GUI)
       └─> sequence_worker.py (Worker)
            ├─> account_switcher.py (Account)
            ├─> ok_watcher.py (Popup)
            └─> job_detector.py (Job)
```

### 2. Vòng lặp chính (sequence_worker.py)
```
while not stopped:
    ├─> Tìm job (job_detector)
    ├─> Click job
    ├─> Thực hiện job
    ├─> Kiểm tra kết quả
    └─> Xử lý popup (ok_watcher)
         └─> Nếu blocked/max job
              └─> Chuyển account (account_switcher)
```

### 3. Xử lý popup (ok_watcher.py)
```
Phát hiện nút OK
  └─> Kiểm tra loại popup (OCR)
       ├─> Max job → Chuyển account
       ├─> Blocked → Lưu file + Chuyển account
       └─> Fail → Báo lỗi
```

### 4. Chuyển account (account_switcher.py)
```
1. Phát hiện popup type (OCR)
2. Lưu account hiện tại vào file
3. Mở menu chọn account
4. Tìm tất cả accounts (4 chiến lược)
5. Lọc bỏ blocked/max job
6. Click account hợp lệ
7. Reset navigation
```

## 🎯 Các thành phần chính

### Controllers (Business Logic)

#### sequence_worker.py
- **Nhiệm vụ**: Điều phối toàn bộ automation
- **Chức năng**:
  - Vòng lặp chính
  - Xử lý jobs
  - Cleanup memory (mỗi 100 vòng)
  - Auto restart LDPlayer (mỗi 800 vòng)

#### account_switcher.py
- **Nhiệm vụ**: Quản lý và chuyển đổi tài khoản
- **Chức năng**:
  - Phát hiện popup (OCR)
  - Tìm tất cả accounts (4 chiến lược)
  - Lọc blocked/max job
  - Chuyển account
  - Lưu file

#### ok_watcher.py
- **Nhiệm vụ**: Giám sát và xử lý popup
- **Chức năng**:
  - Thread riêng chạy liên tục
  - Phát hiện nút OK
  - Phân loại popup
  - Gọi account_switcher khi cần

#### job_detector.py
- **Nhiệm vụ**: Phát hiện và click job
- **Chức năng**:
  - Tìm job icons
  - Click job
  - Scroll để tìm thêm

### Utils (Helpers)

#### adb_utils.py
- **Nhiệm vụ**: Điều khiển LDPlayer qua ADB
- **Chức năng**:
  - Connect ADB
  - Click ảo (tap)
  - Screenshot
  - Mở app
  - Press key

#### image_utils.py
- **Nhiệm vụ**: Xử lý ảnh và template matching
- **Chức năng**:
  - Screenshot
  - Template matching
  - Multiscale matching

#### ocr_utils.py
- **Nhiệm vụ**: Đọc text từ ảnh
- **Chức năng**:
  - EasyOCR (tiếng Việt)
  - Tesseract OCR
  - Preprocess ảnh

### Views (UI)

#### gui.py
- **Nhiệm vụ**: Giao diện người dùng
- **Tabs**:
  1. 📁 Templates - Quản lý template
  2. ⚙️ Cấu hình - Settings
  3. 👥 Tài khoản - Quản lý blocked/max job
  4. ⏰ Hẹn giờ - Tự động tắt máy

## 🔧 Tối ưu đã thực hiện

### 1. Account Detection (4 chiến lược)
- ✅ Template matching (nhiều threshold)
- ✅ Edge detection (tìm khung)
- ✅ Pattern expansion (mở rộng theo khoảng cách)
- ✅ Fixed positions (fallback)

### 2. Popup Detection (OCR)
- ✅ EasyOCR (tiếng Việt)
- ✅ Từ khóa: "không tải được", "100 jobs"
- ✅ Phân loại: blocked vs max job

### 3. Memory Management
- ✅ Garbage collection (mỗi 100 vòng)
- ✅ Clear cache (template, OpenCV, PIL)
- ✅ Auto restart LDPlayer (mỗi 800 vòng)

### 4. Navigation
- ✅ ADB mở Golike (thay vì tìm icon)
- ✅ Bắt buộc tìm "Kiếm tiền" mới tiếp tục
- ✅ Retry với ADB nếu thất bại

## 📊 Data Flow

### Account Data (Models/)
```
Controllers/account_switcher.py
  ├─> Models/blocked_accounts.txt (vĩnh viễn)
  │    Format: 273_265, 274_372, ...
  │    Lưu tài khoản bị Facebook block
  │
  ├─> Models/max_job_accounts.txt (reset mỗi ngày)
  │    Format: 273_484, 274_590, ...
  │    Lưu tài khoản đã làm 100 jobs/ngày
  │
  └─> Models/last_reset_date.txt (ngày reset cuối)
       Format: 2025-12-07
       Dùng để kiểm tra và reset max_job_accounts.txt
```

### Settings Data (Root)
```
gui.py
  └─> settings.json (Root directory)
       ├─> templates: {job_icon: "path", ...}
       ├─> params: {conf_job: 0.85, ...}
       ├─> adb: {use_adb: true, port: 5555, ...}
       └─> timeouts: {job: 8, fb: 8, ...}
```

### Coin Data (Models/)
```
Models/coin_tracker.py
  └─> Models/coins_data.txt
       Format: JSON
       {
         "session_coins": 0,
         "session_jobs": 0,
         "history": [...]
       }
```

## 🚀 Cải tiến trong tương lai

### Nên làm:
1. ✅ Tách Models thành files riêng
2. ✅ Tạo base Controller class
3. ✅ Dependency injection
4. ✅ Event system (thay vì callback)
5. ✅ Logging system (thay vì print)

### Không nên:
1. ❌ Refactor toàn bộ cùng lúc (rủi ro cao)
2. ❌ Thay đổi cấu trúc file lớn (gây lỗi)
3. ❌ Over-engineering (phức tạp không cần thiết)

## 📝 Coding Standards

### Naming Convention
- **Classes**: PascalCase (AccountSwitcher)
- **Functions**: snake_case (find_all_accounts)
- **Constants**: UPPER_CASE (MAX_RETRIES)
- **Private**: _leading_underscore (_internal_method)

### File Organization
- **Imports**: stdlib → third-party → local
- **Classes**: __init__ → public → private
- **Functions**: public → private

### Error Handling
- **Try-except**: Bắt exception cụ thể
- **Logging**: Log lỗi với traceback
- **Fallback**: Luôn có plan B

## 🐛 Debug Tips

### Kiểm tra ADB
```bash
adb devices
adb -s emulator-5554 shell input tap 270 300
```

### Kiểm tra Template
- Threshold quá cao → Không tìm thấy
- Threshold quá thấp → Nhiều false positive
- Optimal: 0.60 - 0.70

### Kiểm tra OCR
- EasyOCR: Tốt cho tiếng Việt
- Tesseract: Tốt cho tiếng Anh
- Preprocess: Tăng contrast, threshold

## 📚 Dependencies

### Core
- tkinter (GUI)
- opencv-python (Image processing)
- pillow (Image handling)
- numpy (Array operations)

### OCR
- easyocr (Tiếng Việt)
- pytesseract (Tiếng Anh)

### ADB
- subprocess (Run ADB commands)

### Optional
- pygetwindow (Window management)
- pyautogui (Keyboard/Mouse)

## 🎓 Best Practices

1. **Single Responsibility**: Mỗi class/function làm 1 việc
2. **DRY**: Don't Repeat Yourself
3. **KISS**: Keep It Simple, Stupid
4. **Error Handling**: Luôn có fallback
5. **Logging**: Log đầy đủ để debug
6. **Testing**: Test từng phần trước khi tích hợp

---

**Lưu ý**: Đây là kiến trúc hiện tại. Refactor dần dần, không làm cùng lúc.


---

## 🎨 MVC Pattern Explained

### Model (Models/)
**Trách nhiệm**: Quản lý data và business rules
- `config.py`: Cấu hình hệ thống (paths, directories)
- `coin_tracker.py`: Logic theo dõi xu
- `*.txt`: Data persistence (blocked accounts, max job accounts)

**Đặc điểm**:
- Không biết về View hay Controller
- Chỉ xử lý data và validation
- Có thể được sử dụng bởi nhiều Controllers

### View (gui.py)
**Trách nhiệm**: Hiển thị UI và nhận input từ user
- Tkinter GUI với 4 tabs
- Hiển thị logs, status, thống kê
- Nhận input (templates, settings, buttons)

**Đặc điểm**:
- Không chứa business logic
- Chỉ gọi Controllers khi cần xử lý
- Update UI dựa trên data từ Models

### Controller (Controllers/)
**Trách nhiệm**: Xử lý business logic và điều phối
- `sequence_worker.py`: Điều phối toàn bộ automation
- `account_switcher.py`: Logic chuyển tài khoản
- `ok_watcher.py`: Xử lý popup
- `job_detector.py`: Phát hiện jobs
- `reset_navigation.py`: Reset điều hướng

**Đặc điểm**:
- Nhận input từ View
- Xử lý business logic
- Cập nhật Models
- Trả kết quả về View

### Utils (Utils/)
**Trách nhiệm**: Helper functions tái sử dụng
- `adb_utils.py`: ADB operations
- `window_utils.py`: Window management
- `image_utils.py`: Image processing
- `ocr_utils.py`: OCR operations
- `navigation.py`: Navigation helpers
- `ldplayer_manager.py`: LDPlayer management

**Đặc điểm**:
- Không chứa business logic
- Stateless (không lưu state)
- Có thể được sử dụng bởi bất kỳ layer nào

## 🔄 Data Flow trong MVC

```
User Input (View)
    ↓
Controller (Process)
    ↓
Model (Update Data)
    ↓
Controller (Get Result)
    ↓
View (Display Result)
```

### Ví dụ: Chuyển tài khoản khi hết job

1. **View** (gui.py): User click "Bắt đầu"
2. **Controller** (sequence_worker.py): Bắt đầu automation loop
3. **Controller** (ok_watcher.py): Phát hiện popup "max job"
4. **Controller** (account_switcher.py): Xử lý chuyển tài khoản
   - Gọi **Utils** (ocr_utils.py): Đọc text popup
   - Gọi **Utils** (image_utils.py): Tìm tài khoản
   - Cập nhật **Model** (max_job_accounts.txt): Lưu tài khoản
5. **View** (gui.py): Hiển thị log "Đã chuyển tài khoản"

## 📦 Dependency Graph

```
main.py
  └─> gui.py (View)
       └─> Controllers/
            ├─> sequence_worker.py
            │    ├─> ok_watcher.py
            │    ├─> job_detector.py
            │    ├─> account_switcher.py
            │    └─> reset_navigation.py
            │
            └─> Utils/
                 ├─> adb_utils.py
                 ├─> window_utils.py
                 ├─> image_utils.py
                 ├─> ocr_utils.py
                 ├─> navigation.py
                 └─> ldplayer_manager.py
```

## 🎯 Lợi ích của MVC

### 1. Separation of Concerns
- Mỗi layer có trách nhiệm riêng
- Dễ hiểu và maintain
- Giảm coupling giữa các components

### 2. Reusability
- Utils có thể dùng lại ở nhiều nơi
- Models có thể dùng cho nhiều Controllers
- Controllers có thể dùng cho nhiều Views

### 3. Testability
- Test từng layer độc lập
- Mock dependencies dễ dàng
- Unit test rõ ràng

### 4. Scalability
- Thêm tính năng mới không ảnh hưởng code cũ
- Refactor từng phần mà không phá vỡ hệ thống
- Team work dễ dàng (chia theo layer)

## 🚀 Best Practices

### 1. Import Order
```python
# Standard library
import os
import time

# Third-party
import cv2
import numpy as np

# Local - Controllers
from Controllers.sequence_worker import SequenceWorker

# Local - Models
from Models.config import load_settings

# Local - Utils
from Utils.adb_utils import ADBController
```

### 2. Naming Conventions
- **Controllers**: `*Worker`, `*Switcher`, `*Detector`, `*Watcher`
- **Models**: `*Tracker`, `Config`
- **Utils**: `*Controller`, `*Manager`, `*_utils`

### 3. File Organization
- **Controllers**: Business logic, orchestration
- **Models**: Data, persistence, validation
- **Utils**: Stateless helpers, no business logic
- **Views**: UI only, no business logic

### 4. Dependency Direction
```
View → Controller → Model
View → Controller → Utils
Controller → Utils
Utils ← (không depend vào layer khác)
```

## 📝 Migration Guide

Nếu cần thêm tính năng mới:

### 1. Thêm Controller mới
```python
# Controllers/new_feature.py
from Utils.adb_utils import ADBController
from Models.config import load_settings

class NewFeature:
    def __init__(self, templates, params, log_fn):
        self.templates = templates
        self.params = params
        self.log_fn = log_fn
    
    def process(self):
        # Business logic here
        pass
```

### 2. Thêm Model mới
```python
# Models/new_data.py
import os
import json

class NewData:
    def __init__(self):
        self.data_file = "Models/new_data.txt"
    
    def load(self):
        # Load data
        pass
    
    def save(self, data):
        # Save data
        pass
```

### 3. Thêm Util mới
```python
# Utils/new_helper.py
def helper_function(param):
    """Stateless helper function"""
    # Process and return
    return result
```

### 4. Cập nhật View
```python
# gui.py
from Controllers.new_feature import NewFeature

def _new_feature_button_click(self):
    feature = NewFeature(self.templates, self.params, self.append_log)
    feature.process()
```

---

**Tóm lại**: Hệ thống đã được tổ chức theo MVC pattern, giúp code dễ đọc, dễ maintain và dễ mở rộng. Mỗi layer có trách nhiệm rõ ràng và không phụ thuộc lẫn nhau một cách không cần thiết.
