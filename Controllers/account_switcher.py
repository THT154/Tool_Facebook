#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Switcher - Tự động chuyển tài khoản khi hết job

CÁCH HOẠT ĐỘNG:
1. Phát hiện popup lỗi bằng OCR (EasyOCR - tốt cho tiếng Việt)
   - Popup blocked: "Không tải được danh sách Job do tài khoản Facebook bị khóa"
   - Popup max job: "Bạn đã làm quá 100 jobs mỗi ngày chắc mệt mỏi lắm rồi"

2. Xác định tài khoản hiện tại:
   - Dùng tọa độ X,Y làm ID (chính xác nhất)
   - Format: 211_205, 273_265, 274_372, etc.
   - Giống format ADB tap: "ADB tap success at (211, 205)"
   - Không dùng OCR (vì OCR kém với tiếng Việt)

3. Lưu tài khoản:
   - Blocked → blocked_accounts.txt (vĩnh viễn)
     Ví dụ: 273_265, 274_372
   - Max job → max_job_accounts.txt (reset mỗi ngày)
     Ví dụ: 273_484, 274_590

4. Chuyển tài khoản:
   - Tìm tất cả tài khoản trong danh sách
   - Lọc bỏ: tài khoản hiện tại, blocked, max job
   - Click vào tài khoản hợp lệ đầu tiên
   - Reset navigation về trang "Kiếm thưởng"

5. Khởi tạo khi bật tool:
   - Mở menu chọn tài khoản
   - Tìm tài khoản tốt nhất (không blocked, không max job)
   - Click vào tài khoản đó để kích hoạt và load job
"""
import os
import time
import random
from Utils.image_utils import load_gray, locate_template, locate_template_multiscale
from Utils.window_utils import click_at
from Models.config import get_template_path

class AccountSwitcher:
    """Class xử lý chuyển tài khoản"""
    
    def __init__(self, templates, params, log_fn):
        self.templates = templates
        self.params = params
        self.log_fn = log_fn
        
        # Tên tài khoản hiện tại (lưu khi bắt đầu chạy tool)
        self.current_account_name = None
        
        # File lưu tài khoản
        self.blocked_accounts_file = "Models/blocked_accounts.txt"  # Vĩnh viễn
        self.max_job_accounts_file = "Models/max_job_accounts.txt"  # Tạm thời (reset mỗi ngày)
        
        # Load danh sách
        self.blocked_accounts = self._load_blocked_accounts()
        self.max_job_accounts = self._load_max_job_accounts()
        
        # Kiểm tra và reset file max_job nếu qua ngày mới
        self._check_and_reset_daily()
        
        # Flag để báo hiệu cần dừng tool
        self.should_stop_tool = False
    
    def initialize_current_account(self):
        """
        Khởi tạo: Đọc ID tài khoản hiện tại khi bắt đầu chạy tool
        
        QUAN TRỌNG: Sau khi mở menu, phải click lại vào tài khoản để:
        - Đóng menu
        - Trigger load job (nếu không click sẽ không load job)
        
        Gọi method này TRƯỚC khi bắt đầu chạy automation
        """
        try:
            self.log_fn("🔍 Đang xác định và kích hoạt tài khoản...")
            
            # Mở menu chọn tài khoản
            if not self.open_account_selector():
                self.log_fn("⚠️ Không mở được menu chọn tài khoản")
                return False
            
            time.sleep(2.0)  # Đợi menu hiện ra
            
            # Tìm tất cả tài khoản
            all_accounts = self.find_all_accounts()
            
            if not all_accounts:
                self.log_fn("⚠️ Không tìm thấy tài khoản nào trong danh sách")
                return False
            
            # Sắp xếp theo Y
            all_accounts.sort(key=lambda a: a[1])
            
            # Tìm tài khoản tốt nhất (không bị blocked, không max job)
            best_account = None
            
            for x, y, score in all_accounts:
                account_id = f"{x}_{y}"
                
                # Kiểm tra xem có bị blocked hoặc max job không
                if account_id in self.blocked_accounts:
                    self.log_fn(f"   ⚠️ {account_id} bị blocked - Bỏ qua")
                    continue
                
                if account_id in self.max_job_accounts:
                    self.log_fn(f"   ⚠️ {account_id} đã max job hôm nay - Bỏ qua")
                    continue
                
                # Tài khoản hợp lệ
                best_account = (x, y, account_id)
                break
            
            if not best_account:
                # Không có tài khoản hợp lệ → Dùng tài khoản đầu tiên
                self.log_fn("   ⚠️ Không có tài khoản hợp lệ, dùng tài khoản đầu tiên")
                x, y, score = all_accounts[0]
                account_id = f"{x}_{y}"
                best_account = (x, y, account_id)
            
            x, y, account_id = best_account
            
            # Lưu ID tài khoản
            self.current_account_name = account_id
            self.log_fn(f"✓ Tài khoản được chọn: {account_id} (tọa độ: {x}, {y})")
            
            # QUAN TRỌNG: Click vào tài khoản để đóng menu và trigger load job
            self.log_fn(f"   🖱️ Click vào tài khoản để kích hoạt...")
            from Utils.window_utils import click_at
            click_at(x, y)
            time.sleep(2.0)  # Đợi load job
            
            self.log_fn(f"✓ Đã kích hoạt tài khoản {account_id}")
            
            return True
                
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi khởi tạo tài khoản: {e}")
            import traceback
            self.log_fn(f"   {traceback.format_exc()}")
            return False
    
    def detect_error_popup_type(self):
        """
        Phát hiện loại popup lỗi bằng cách đọc NỘI DUNG TEXT trong popup
        
        CHIẾN LƯỢC:
        - Các popup có bố cục giống nhau, chỉ khác nội dung
        - Dùng EasyOCR đọc text trong popup (tốt cho tiếng Việt)
        - Tìm từ khóa để phân loại
        
        Popup blocked: "Không tải được danh sách Job do tài khoản Facebook bị khóa"
        Popup max job: "Bạn đã làm quá 100 jobs mỗi ngày chắc mệt mỏi lắm rồi"
        
        Returns: 
            'max_job' - Đã làm tối đa job
            'blocked' - Tài khoản bị block
            'error' - Lỗi khác
            None - Không có popup
        """
        try:
            from Utils.image_utils import screenshot_gray
            from Utils.ocr_utils import extract_text_from_image, check_ocr_available, get_easyocr_reader
            import cv2
            import numpy as np
            
            # Kiểm tra OCR có sẵn không
            if not check_ocr_available():
                self.log_fn(f"   ⚠️ OCR không khả dụng - Không thể phân loại popup")
                return None
            
            # Chụp màn hình
            screen = screenshot_gray()
            if screen is None:
                return None
            
            h, w = screen.shape[:2]
            
            # Crop vùng popup (giữa màn hình)
            # Popup thường ở: 20-70% chiều cao, 10-90% chiều rộng
            x1 = int(w * 0.10)   # 10% từ trái
            y1 = int(h * 0.20)   # 20% từ trên
            x2 = int(w * 0.90)   # 90% từ trái
            y2 = int(h * 0.70)   # 70% từ trên
            
            popup_region = screen[y1:y2, x1:x2]
            
            # Tiền xử lý ảnh để OCR tốt hơn
            # 1. Tăng contrast
            enhanced = cv2.convertScaleAbs(popup_region, alpha=2.0, beta=10)
            
            # 2. Threshold để làm nổi text
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 3. Thử cả invert (nếu text màu sáng trên nền tối)
            _, binary_inv = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Thử OCR cả 2 ảnh
            all_text = []
            
            for img in [binary, binary_inv, enhanced]:
                text = extract_text_from_image(img, prefer_easyocr=True)
                if text:
                    all_text.append(text)
            
            # Gộp tất cả text lại
            combined_text = ' '.join(all_text)
            
            if not combined_text:
                self.log_fn(f"   ⚠️ OCR không đọc được text trong popup")
                return None
            
            # Làm sạch và chuẩn hóa text
            combined_text = combined_text.lower()
            combined_text = combined_text.replace('\n', ' ').replace('\r', ' ')
            
            # Log text đọc được (giới hạn 200 ký tự)
            self.log_fn(f"   📝 OCR popup: '{combined_text[:200]}...'")
            
            # PHÂN LOẠI DỰA TRÊN TỪ KHÓA
            
            # 1. BLOCKED (ƯU TIÊN KIỂM TRA TRƯỚC)
            # Từ khóa chính xác từ popup: "Không tải được danh sách Job do tài khoản Facebook bị khóa"
            blocked_keywords = [
                'không tải được',           # Từ khóa chính
                'facebook bị khóa',         # Từ khóa chính
                'danh sách job',            # Từ khóa chính
                'tài khoản facebook bị',    # Từ khóa phụ
                'khóa',                     # Từ khóa phụ
                'block',                    # Từ khóa phụ
                'bị chặn',                  # Từ khóa phụ
            ]
            
            # Đếm số từ khóa blocked tìm thấy
            blocked_count = sum(1 for k in blocked_keywords if k in combined_text)
            
            if blocked_count >= 2:  # Cần ít nhất 2 từ khóa để chắc chắn
                self.log_fn(f"🔒 Phát hiện popup 'Tài khoản bị block' ({blocked_count} từ khóa)")
                return 'blocked'
            
            # 2. MAX JOB
            # Từ khóa chính xác từ popup: "Bạn đã làm quá 100 jobs mỗi ngày chắc mệt mỏi lắm rồi"
            max_job_keywords = [
                '100 jobs',                 # Từ khóa chính
                'quá 100',                  # Từ khóa chính
                'làm quá 100',              # Từ khóa chính
                'mỗi ngày',                 # Từ khóa phụ
                'chắc mệt',                 # Từ khóa phụ
                'mệt mỏi',                  # Từ khóa phụ
                '100',                      # Từ khóa số
            ]
            
            # Đếm số từ khóa max job tìm thấy
            max_job_count = sum(1 for k in max_job_keywords if k in combined_text)
            
            if max_job_count >= 2:  # Cần ít nhất 2 từ khóa
                self.log_fn(f"🚫 Phát hiện popup 'Đã làm tối đa job' ({max_job_count} từ khóa)")
                return 'max_job'
            
            # 3. Nếu chỉ có 1 từ khóa, ưu tiên blocked (vì nghiêm trọng hơn)
            if blocked_count >= 1:
                self.log_fn(f"🔒 Có thể là popup 'Tài khoản bị block' ({blocked_count} từ khóa)")
                return 'blocked'
            
            if max_job_count >= 1:
                self.log_fn(f"🚫 Có thể là popup 'Đã làm tối đa job' ({max_job_count} từ khóa)")
                return 'max_job'
            
            # 4. Lỗi chung
            error_keywords = ['lỗi', 'error', 'thất bại', 'failed']
            if any(k in combined_text for k in error_keywords):
                self.log_fn(f"⚠️ Phát hiện popup lỗi chung")
                return 'error'
            
            # Không phân loại được
            self.log_fn(f"   ❓ Không phân loại được popup (text không khớp từ khóa)")
            return None
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi phát hiện popup: {e}")
            import traceback
            self.log_fn(f"   {traceback.format_exc()}")
            return None
    
    def click_ok_button(self):
        """Click nút OK trong popup"""
        try:
            ok_path = self.templates.get('ok_button')
            if ok_path:
                tmpl = load_gray(ok_path)
                found = locate_template(
                    tmpl, confidence=0.85, timeout=2.0,
                    step=0.08, region=None
                )
                
                if found:
                    x, y, _ = found
                    self.log_fn("   ✓ Click nút OK")
                    click_at(x, y)
                    time.sleep(1.0)
                    return True
            
            self.log_fn("   ⚠️ Không tìm thấy nút OK")
            return False
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi click OK: {e}")
            return False
    
    def open_account_selector(self):
        """
        Mở menu chọn tài khoản (click vào avatar/tên góc trên phải)
        Returns: True nếu thành công
        """
        try:
            # Tìm template "Chọn tài khoản" hoặc avatar
            selector_keys = ['account_selector', 'chon_tai_khoan', 'avatar_button']
            
            for key in selector_keys:
                if key in self.templates:
                    template_path = get_template_path(self.templates[key])
                    try:
                        tmpl = load_gray(template_path)
                        found = locate_template(
                            tmpl, confidence=0.80, timeout=2.0,
                            step=0.08, region=None
                        )
                        
                        if found:
                            x, y, _ = found
                            self.log_fn(f"   ✓ Tìm thấy '{key}' → Click")
                            click_at(x, y)
                            time.sleep(1.5)
                            return True
                    except Exception as e:
                        self.log_fn(f"   ⚠️ Lỗi khi tìm '{key}': {e}")
            
            self.log_fn("   ⚠️ Không tìm thấy nút chọn tài khoản")
            return False
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi mở account selector: {e}")
            return False
    
    def detect_current_account_name_from_header(self):
        """
        Đọc tên tài khoản hiện tại từ header (góc trên phải)
        
        Tài khoản hiện tại hiển thị bên phải nút "Chọn tài khoản"
        Ví dụ: "Kiếm Tiền", "Account123", v.v.
        
        Returns: Tên tài khoản hoặc None
        """
        try:
            from Utils.image_utils import screenshot_gray
            from Utils.ocr_utils import extract_text_from_image, check_ocr_available
            import cv2
            
            if not check_ocr_available():
                self.log_fn("   ⚠️ OCR không khả dụng")
                return None
            
            # Chụp màn hình
            screen = screenshot_gray()
            if screen is None:
                return None
            
            h, w = screen.shape[:2]
            
            # Crop vùng header (góc trên phải)
            # Tài khoản hiện tại thường ở: 50-100% chiều rộng, 0-15% chiều cao
            x1 = int(w * 0.5)   # 50% từ trái
            y1 = 0
            x2 = w
            y2 = int(h * 0.15)  # 15% từ trên
            
            header_region = screen[y1:y2, x1:x2]
            
            # Tiền xử lý để OCR tốt hơn
            # 1. Tăng contrast
            enhanced = cv2.convertScaleAbs(header_region, alpha=2.0, beta=10)
            
            # 2. Threshold
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 3. Thử cả invert
            _, binary_inv = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # OCR cả 2 ảnh
            for img in [binary, binary_inv]:
                text = extract_text_from_image(img)
                
                if text:
                    # Làm sạch text
                    text = text.strip().replace('\n', ' ').replace('\r', '')
                    
                    # Tìm tên tài khoản (bỏ qua các text khác như "Chọn tài khoản")
                    # Tên tài khoản thường ngắn, không có dấu cách nhiều
                    words = text.split()
                    
                    # Lọc bỏ các từ không phải tên tài khoản
                    skip_words = ['chọn', 'tài', 'khoản', 'select', 'account', 'menu']
                    
                    for word in words:
                        word_lower = word.lower()
                        # Bỏ qua từ khóa
                        if any(skip in word_lower for skip in skip_words):
                            continue
                        
                        # Nếu từ có ít nhất 3 ký tự và có chữ/số
                        if len(word) >= 3 and any(c.isalnum() for c in word):
                            self.log_fn(f"   📝 Tên tài khoản từ header: '{word}'")
                            return word
            
            self.log_fn("   ⚠️ Không đọc được tên tài khoản từ header")
            return None
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi đọc tên từ header: {e}")
            return None
    
    def detect_current_account_position_in_list(self):
        """
        Phát hiện vị trí tài khoản hiện tại trong danh sách
        
        CHIẾN LƯỢC ĐƠN GIẢN:
        - Tìm tất cả tài khoản bằng template matching
        - Tài khoản đầu tiên (y nhỏ nhất) là tài khoản hiện tại
        
        Returns: (x, y) hoặc None
        """
        try:
            # Tìm tất cả tài khoản
            all_accounts = self.find_all_accounts()
            
            if not all_accounts:
                self.log_fn(f"   ⚠️ Không tìm thấy tài khoản nào")
                return None
            
            # Sắp xếp theo Y (từ trên xuống)
            all_accounts.sort(key=lambda a: a[1])
            
            # Tài khoản đầu tiên (trên cùng) là tài khoản hiện tại
            x, y, score = all_accounts[0]
            
            self.log_fn(f"   ✓ Tài khoản hiện tại tại ({x}, {y}) (tài khoản đầu tiên)")
            return (x, y)
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi phát hiện vị trí: {e}")
            return None
    
    def detect_current_account(self):
        """
        Phát hiện tài khoản hiện tại
        
        Returns: Tọa độ của tài khoản hiện tại hoặc None
        """
        try:
            # Thử phát hiện bằng màu (tài khoản tô đỏ/hồng)
            pos = self.detect_current_account_position_in_list()
            
            if pos:
                return pos
            
            # Fallback: Trả về tọa độ giả
            return (0, 0)
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi phát hiện tài khoản hiện tại: {e}")
            return None
    
    def find_all_accounts(self):
        """
        Tìm tất cả tài khoản trong danh sách - NÂNG CẤP
        
        CHIẾN LƯỢC KẾT HỢP:
        1. Template matching với nhiều threshold
        2. Phát hiện bằng edge detection (tìm khung)
        3. Phát hiện bằng khoảng cách đều (pattern)
        4. Fallback: Vị trí cố định
        
        Returns: List các tọa độ [(x1, y1, score1), (x2, y2, score2), ...]
        """
        try:
            from Utils.image_utils import screenshot_gray
            from Utils.window_utils import is_adb_mode
            from Utils.adb_utils import get_adb_controller
            import cv2
            import numpy as np
            
            # CHIẾN LƯỢC 1: Template matching với nhiều threshold
            accounts = self._find_accounts_by_template()
            
            if accounts and len(accounts) >= 3:
                # Đủ tài khoản → Trả về
                return accounts
            
            # CHIẾN LƯỢC 2: Phát hiện bằng edge detection
            self.log_fn(f"   🔍 Thử phát hiện bằng edge detection...")
            accounts_edge = self._find_accounts_by_edges()
            
            if accounts_edge and len(accounts_edge) > len(accounts):
                self.log_fn(f"   ✓ Edge detection tìm thấy nhiều hơn: {len(accounts_edge)} tài khoản")
                return accounts_edge
            
            # CHIẾN LƯỢC 3: Phát hiện bằng pattern (khoảng cách đều)
            if accounts and len(accounts) >= 2:
                self.log_fn(f"   🔍 Thử mở rộng bằng pattern...")
                accounts_pattern = self._expand_accounts_by_pattern(accounts)
                if len(accounts_pattern) > len(accounts):
                    self.log_fn(f"   ✓ Pattern detection tìm thêm: {len(accounts_pattern)} tài khoản")
                    return accounts_pattern
            
            # CHIẾN LƯỢC 4: Fallback - Vị trí cố định
            if not accounts:
                self.log_fn(f"   💡 Fallback → Dùng vị trí cố định")
                return self._get_fixed_positions()
            
            return accounts
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi tìm tất cả tài khoản: {e}")
            import traceback
            self.log_fn(f"   {traceback.format_exc()}")
            return []
    
    def _find_accounts_by_template(self):
        """Tìm tài khoản bằng template matching"""
        try:
            from Utils.image_utils import screenshot_gray
            import cv2
            import numpy as np
            
            account_keys = ['account_item', 'tai_khoan_item', 'account_list_item']
            
            for key in account_keys:
                if key not in self.templates:
                    continue
                
                template_path = get_template_path(self.templates[key])
                if not os.path.exists(template_path):
                    continue
                
                self.log_fn(f"   🔍 Template matching với '{key}'...")
                
                tmpl = load_gray(template_path)
                screen = screenshot_gray()
                
                if screen is None or tmpl is None:
                    continue
                
                # Thử nhiều threshold
                thresholds = [0.65, 0.60, 0.55, 0.50]
                
                for threshold in thresholds:
                    result = cv2.matchTemplate(screen, tmpl, cv2.TM_CCOEFF_NORMED)
                    locations = np.where(result >= threshold)
                    
                    if len(locations[0]) == 0:
                        continue
                    
                    # Lấy tọa độ
                    accounts = []
                    h, w = tmpl.shape[:2]
                    
                    for pt in zip(*locations[::-1]):
                        x, y = pt
                        score = result[y, x]
                        center_x = x + w // 2
                        center_y = y + h // 2
                        accounts.append((center_x, center_y, score))
                    
                    # Loại bỏ duplicate (gần nhau trong vòng 40px)
                    filtered = self._remove_duplicates(accounts, distance=40)
                    
                    if len(filtered) >= 3:
                        self.log_fn(f"   ✓ Tìm thấy {len(filtered)} tài khoản (threshold={threshold})")
                        for i, (x, y, score) in enumerate(filtered, 1):
                            self.log_fn(f"      Tài khoản {i}: ({x}, {y}) score={score:.2f}")
                        return filtered
                
            return []
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi template matching: {e}")
            return []
    
    def _find_accounts_by_edges(self):
        """Tìm tài khoản bằng edge detection (tìm khung)"""
        try:
            from Utils.image_utils import screenshot_gray
            import cv2
            import numpy as np
            
            screen = screenshot_gray()
            if screen is None:
                return []
            
            # Edge detection
            edges = cv2.Canny(screen, 50, 150)
            
            # Tìm contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Lọc contours có kích thước phù hợp (khung tài khoản)
            h, w = screen.shape[:2]
            min_width = int(w * 0.6)  # Ít nhất 60% chiều rộng
            max_width = int(w * 0.95)
            min_height = 60
            max_height = 120
            
            accounts = []
            for contour in contours:
                x, y, cw, ch = cv2.boundingRect(contour)
                
                # Kiểm tra kích thước
                if min_width <= cw <= max_width and min_height <= ch <= max_height:
                    center_x = x + cw // 2
                    center_y = y + ch // 2
                    accounts.append((center_x, center_y, 0.8))
            
            # Loại bỏ duplicate
            filtered = self._remove_duplicates(accounts, distance=40)
            
            if filtered:
                self.log_fn(f"   ✓ Edge detection: {len(filtered)} tài khoản")
            
            return filtered
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi edge detection: {e}")
            return []
    
    def _expand_accounts_by_pattern(self, accounts):
        """Mở rộng danh sách tài khoản dựa trên pattern (khoảng cách đều)"""
        try:
            if len(accounts) < 2:
                return accounts
            
            # Sắp xếp theo Y
            sorted_accounts = sorted(accounts, key=lambda a: a[1])
            
            # Tính khoảng cách trung bình
            distances = []
            for i in range(len(sorted_accounts) - 1):
                dist = sorted_accounts[i+1][1] - sorted_accounts[i][1]
                distances.append(dist)
            
            avg_distance = sum(distances) / len(distances)
            
            # Mở rộng lên trên và xuống dưới
            expanded = list(sorted_accounts)
            
            # Mở rộng lên trên
            first_x, first_y, _ = sorted_accounts[0]
            for i in range(1, 3):  # Thử thêm 2 tài khoản phía trên
                new_y = first_y - (avg_distance * i)
                if new_y > 100:  # Không quá gần đầu màn hình
                    expanded.append((first_x, int(new_y), 0.7))
            
            # Mở rộng xuống dưới
            last_x, last_y, _ = sorted_accounts[-1]
            for i in range(1, 3):  # Thử thêm 2 tài khoản phía dưới
                new_y = last_y + (avg_distance * i)
                if new_y < 800:  # Không quá gần cuối màn hình
                    expanded.append((last_x, int(new_y), 0.7))
            
            # Loại bỏ duplicate và sắp xếp
            filtered = self._remove_duplicates(expanded, distance=40)
            filtered.sort(key=lambda a: a[1])
            
            return filtered
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi pattern expansion: {e}")
            return accounts
    
    def _remove_duplicates(self, accounts, distance=40):
        """Loại bỏ tài khoản trùng lặp (gần nhau)"""
        filtered = []
        for acc in accounts:
            x, y, score = acc
            is_duplicate = False
            
            for existing in filtered:
                ex, ey, _ = existing
                if abs(x - ex) < distance and abs(y - ey) < distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(acc)
        
        # Sắp xếp theo Y
        filtered.sort(key=lambda a: a[1])
        return filtered
    
    def _get_fixed_positions(self):
        """Lấy vị trí cố định (fallback cuối cùng)"""
        try:
            from Utils.window_utils import is_adb_mode
            from Utils.adb_utils import get_adb_controller
            
            if is_adb_mode():
                controller = get_adb_controller()
                screen_size = controller.get_screen_size()
                
                if screen_size:
                    w, h = screen_size
                    center_x = w // 2
                    
                    # 5 tài khoản, cách nhau 110px
                    accounts = []
                    start_y = 220
                    for i in range(5):
                        y = start_y + (i * 110)
                        accounts.append((center_x, y, 1.0))
                    
                    self.log_fn(f"   ✓ Tạo {len(accounts)} vị trí cố định")
                    return accounts
            
            return []
            
        except Exception:
            return []
    
    def select_different_account(self, current_pos=None):
        """
        Chọn tài khoản khác (không phải tài khoản hiện tại, không phải blocked, không phải max job)
        Args:
            current_pos: Tọa độ tài khoản hiện tại (x, y)
        Returns: True nếu thành công
        """
        try:
            # CHIẾN LƯỢC: Tìm tất cả tài khoản bằng template matching
            all_accounts = self.find_all_accounts()
            
            if not all_accounts:
                self.log_fn("   ⚠️ Không tìm thấy tài khoản nào bằng template")
                self.log_fn("   💡 Fallback: Click vào vị trí cố định...")
                
                # Fallback: Click vào vị trí cố định
                from Utils.window_utils import is_adb_mode
                from Utils.adb_utils import get_adb_controller
                
                if is_adb_mode():
                    controller = get_adb_controller()
                    screen_size = controller.get_screen_size()
                    
                    if screen_size:
                        w, h = screen_size
                        center_x = w // 2
                        
                        # Click vào tài khoản thứ 2 (giả sử)
                        fallback_y = h // 3 + 100
                        self.log_fn(f"   ✓ Click fallback tại ({center_x}, {fallback_y})")
                        click_at(center_x, fallback_y)
                        time.sleep(2.0)
                        return True
                
                return False
            
            # Lọc bỏ tài khoản hiện tại
            available_accounts = all_accounts
            
            if current_pos:
                cx, cy = current_pos
                current_id = f"{cx}_{cy}"
                self.log_fn(f"   ℹ️ Tài khoản hiện tại: {current_id}")
                
                # Lọc bỏ tài khoản trùng với current_pos (so sánh cả X và Y)
                available_accounts = [
                    (x, y, score) for x, y, score in all_accounts
                    if abs(x - cx) > 20 or abs(y - cy) > 20  # Cho phép sai số 20px
                ]
                
                self.log_fn(f"   ℹ️ Còn {len(available_accounts)} tài khoản khác")
            
            # Lọc bỏ tài khoản blocked và max job
            if len(self.blocked_accounts) > 0 or len(self.max_job_accounts) > 0:
                self.log_fn(f"   🔍 Lọc tài khoản blocked ({len(self.blocked_accounts)}) và max job ({len(self.max_job_accounts)})...")
                
                valid_accounts = []
                for x, y, score in available_accounts:
                    # Lấy ID tài khoản (dựa trên Y)
                    account_id = self.get_account_id_from_position(x, y)
                    
                    if account_id:
                        # Kiểm tra xem có trong danh sách blocked hoặc max job không
                        if account_id in self.blocked_accounts:
                            self.log_fn(f"      ✗ Bỏ qua {account_id} (blocked)")
                            continue
                        
                        if account_id in self.max_job_accounts:
                            self.log_fn(f"      ✗ Bỏ qua {account_id} (max job hôm nay)")
                            continue
                        
                        self.log_fn(f"      ✓ {account_id} hợp lệ")
                        valid_accounts.append((x, y, score, account_id))
                    else:
                        # Không lấy được ID → Vẫn thêm vào (fallback)
                        self.log_fn(f"      ? Không xác định được tại ({x}, {y}) - Vẫn thêm vào")
                        valid_accounts.append((x, y, score, None))
            else:
                # Không có tài khoản nào bị chặn → Dùng tất cả
                valid_accounts = [(x, y, score, None) for x, y, score in available_accounts]
            
            if not valid_accounts:
                self.log_fn("   ⚠️ Không có tài khoản hợp lệ để chuyển")
                self.log_fn("   ❌ TẤT CẢ TÀI KHOẢN ĐÃ BỊ BLOCKED HOẶC MAX JOB!")
                self.log_fn("   🛑 Tool sẽ dừng lại...")
                
                # Set flag để dừng tool
                self.should_stop_tool = True
                self._stop_tool()
                
                return False
            
            # Chọn tài khoản đầu tiên hợp lệ
            x, y, score, account_id = valid_accounts[0]
            id_str = f"{account_id}" if account_id else f"{x}_{y}"
            self.log_fn(f"   ✓ Chọn tài khoản {id_str} tại ({x}, {y}) score={score:.2f}")
            
            # CẬP NHẬT ID TRƯỚC KHI CLICK (vì sau khi click menu đóng, không tìm được template)
            if account_id:
                self.current_account_name = account_id
                self.log_fn(f"   ✓ Đã cập nhật ID tài khoản mới: {account_id}")
            
            click_at(x, y)
            time.sleep(2.0)
            return True
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi chọn tài khoản: {e}")
            import traceback
            self.log_fn(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def switch_account(self, skip_ok_button=False):
        """
        Thực hiện chuyển tài khoản
        Args:
            skip_ok_button: Bỏ qua bước click OK (đã click rồi)
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            self.log_fn("🔄 Bắt đầu chuyển tài khoản...")
            
            # 1. Click OK để đóng popup (nếu chưa click)
            if not skip_ok_button:
                self.log_fn("   [1/4] Đóng popup...")
                if not self.click_ok_button():
                    self.log_fn("   ⚠️ Không đóng được popup, tiếp tục...")
                time.sleep(1.0)
            else:
                self.log_fn("   [1/4] Bỏ qua đóng popup (đã đóng)")
            
            # 2. Mở menu chọn tài khoản
            self.log_fn("   [2/4] Mở menu chọn tài khoản...")
            if not self.open_account_selector():
                self.log_fn("   ❌ Không mở được menu chọn tài khoản")
                return False
            
            # Đợi menu hiện ra hoàn toàn
            self.log_fn("   ⏳ Đợi menu hiện ra (2 giây)...")
            time.sleep(2.0)
            
            # 3. Phát hiện tài khoản hiện tại
            self.log_fn("   [3/4] Phát hiện tài khoản hiện tại...")
            current_pos = self.detect_current_account()
            if current_pos:
                self.log_fn(f"   ✓ Tài khoản hiện tại: {current_pos}")
            else:
                self.log_fn("   ⚠️ Không phát hiện được tài khoản hiện tại (sẽ chọn tài khoản thứ 2)")
            
            # 4. Chọn tài khoản khác (không phải blocked)
            self.log_fn("   [4/4] Chọn tài khoản khác...")
            success = self.select_different_account(current_pos)
            
            if not success:
                self.log_fn("   ❌ Không chọn được tài khoản khác")
                return False
            
            # Đợi chuyển tài khoản
            self.log_fn("   ⏳ Đợi chuyển tài khoản (3 giây)...")
            time.sleep(3.0)
            
            self.log_fn("✅ Đã chuyển tài khoản thành công!")
            return True
            
        except Exception as e:
            self.log_fn(f"❌ Lỗi khi chuyển tài khoản: {e}")
            import traceback
            self.log_fn(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def handle_error_popup(self):
        """
        Xử lý popup lỗi dựa trên loại
        Returns: 
            'switched' - Đã chuyển tài khoản
            'blocked' - Tài khoản bị block và đã xử lý
            'error' - Lỗi khác, đã click OK
            None - Không có popup
        """
        try:
            # Phát hiện loại popup
            popup_type = self.detect_error_popup_type()
            
            if popup_type is None:
                return None
            
            if popup_type == 'max_job':
                # Tài khoản hết job → Chuyển tài khoản
                self.log_fn("🔄 Tài khoản đã hết job - Chuyển sang tài khoản khác...")
                
                # Click OK
                self.click_ok_button()
                time.sleep(1.0)
                
                # Chuyển tài khoản
                success = self.switch_account(skip_ok_button=True)
                
                if success:
                    return 'switched'
                else:
                    return 'error'
            
            elif popup_type == 'blocked':
                # Tài khoản bị block → Lưu vào file và chuyển
                self.log_fn("🔒 Tài khoản bị block - Lưu vào danh sách và chuyển...")
                
                success = self.handle_blocked_account()
                
                if success:
                    return 'blocked'
                else:
                    return 'error'
            
            else:  # popup_type == 'error'
                # Lỗi khác → Chỉ click OK
                self.log_fn("⚠️ Popup lỗi khác - Click OK và tiếp tục...")
                self.click_ok_button()
                time.sleep(1.0)
                return 'error'
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi xử lý popup: {e}")
            return None
    
    def _load_blocked_accounts(self):
        """Load danh sách tài khoản bị block từ file (vĩnh viễn)"""
        try:
            if os.path.exists(self.blocked_accounts_file):
                with open(self.blocked_accounts_file, 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                    if accounts:
                        self.log_fn(f"📋 Đã load {len(accounts)} tài khoản bị block (vĩnh viễn)")
                    return set(accounts)
            return set()
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi load blocked accounts: {e}")
            return set()
    
    def _load_max_job_accounts(self):
        """Load danh sách tài khoản đã max job từ file (tạm thời)"""
        try:
            if os.path.exists(self.max_job_accounts_file):
                with open(self.max_job_accounts_file, 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                    if accounts:
                        self.log_fn(f"📋 Đã load {len(accounts)} tài khoản đã max job (hôm nay)")
                    return set(accounts)
            return set()
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi load max job accounts: {e}")
            return set()
    
    def _stop_tool(self):
        """
        Hiển thị thông báo khi không còn tài khoản hợp lệ
        Sequence worker sẽ kiểm tra và dừng
        """
        try:
            self.log_fn("")
            self.log_fn("=" * 60)
            self.log_fn("🛑 KHÔNG CÒN TÀI KHOẢN HỢP LỆ")
            self.log_fn("=" * 60)
            self.log_fn(f"📊 Thống kê:")
            self.log_fn(f"   - Tài khoản bị blocked: {len(self.blocked_accounts)}")
            self.log_fn(f"   - Tài khoản max job hôm nay: {len(self.max_job_accounts)}")
            self.log_fn("")
            
            if self.blocked_accounts:
                self.log_fn(f"🔒 Danh sách blocked:")
                for acc_id in sorted(self.blocked_accounts):
                    self.log_fn(f"   - {acc_id}")
            
            if self.max_job_accounts:
                self.log_fn(f"🚫 Danh sách max job:")
                for acc_id in sorted(self.max_job_accounts):
                    self.log_fn(f"   - {acc_id}")
            
            self.log_fn("")
            self.log_fn("💡 Giải pháp:")
            self.log_fn("   - Chờ sang ngày mai để reset danh sách max job")
            self.log_fn("   - Hoặc thêm tài khoản mới vào app")
            self.log_fn("=" * 60)
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi hiển thị thông báo: {e}")
    
    def _check_in_golike_app(self):
        """
        Kiểm tra xem có đang trong app Golike không
        Returns: True nếu đang trong app, False nếu không
        """
        try:
            # Tìm icon/logo đặc trưng của Golike
            golike_keys = ['golike_icon', 'golike_logo', 'app_header']
            
            for key in golike_keys:
                if key in self.templates:
                    template_path = get_template_path(self.templates[key])
                    if os.path.exists(template_path):
                        try:
                            tmpl = load_gray(template_path)
                            found = locate_template(
                                tmpl, confidence=0.75, timeout=1.0,
                                step=0.08, region=None
                            )
                            
                            if found:
                                return True
                        except Exception:
                            pass
            
            return False
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi kiểm tra Golike app: {e}")
            return False
    
    def _check_in_earn_page(self):
        """
        Kiểm tra xem có đang ở trang 'Kiếm thưởng' (load job) không
        Returns: True nếu đang ở đúng trang, False nếu không
        """
        try:
            # Tìm header/icon đặc trưng của trang Kiếm thưởng
            earn_page_keys = ['earn_page_header', 'earn_button', 'kiem_thuong_header']
            
            for key in earn_page_keys:
                if key in self.templates:
                    template_path = get_template_path(self.templates[key])
                    if os.path.exists(template_path):
                        try:
                            tmpl = load_gray(template_path)
                            found = locate_template(
                                tmpl, confidence=0.75, timeout=1.0,
                                step=0.08, region=None
                            )
                            
                            if found:
                                return True
                        except Exception:
                            pass
            
            return False
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi kiểm tra trang Kiếm thưởng: {e}")
            return False
    
    def _check_and_reset_daily(self):
        """Kiểm tra và reset file max_job nếu qua ngày mới"""
        try:
            import datetime
            
            # File lưu ngày cuối cùng reset
            last_reset_file = "Models/last_reset_date.txt"
            today = datetime.date.today().isoformat()
            
            # Đọc ngày reset cuối cùng
            last_reset_date = None
            if os.path.exists(last_reset_file):
                with open(last_reset_file, 'r') as f:
                    last_reset_date = f.read().strip()
            
            # Nếu khác ngày → Reset
            if last_reset_date != today:
                self.log_fn(f"🌅 Ngày mới ({today}) - Reset danh sách tài khoản max job")
                
                # Xóa file max_job_accounts
                if os.path.exists(self.max_job_accounts_file):
                    os.remove(self.max_job_accounts_file)
                
                # Reset set
                self.max_job_accounts = set()
                
                # Lưu ngày mới
                with open(last_reset_file, 'w') as f:
                    f.write(today)
                
                self.log_fn(f"   ✓ Đã reset danh sách max job accounts")
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi check reset daily: {e}")
    
    def _save_blocked_account(self, account_id):
        """
        Lưu tài khoản bị block vào file (vĩnh viễn)
        Args:
            account_id: ID tài khoản dạng "Y_265", "Y_372", etc.
        """
        try:
            if account_id in self.blocked_accounts:
                self.log_fn(f"   ℹ️ {account_id} đã có trong danh sách block")
                return
            
            self.blocked_accounts.add(account_id)
            
            with open(self.blocked_accounts_file, 'a', encoding='utf-8') as f:
                f.write(f"{account_id}\n")
            
            self.log_fn(f"   ✓ Đã lưu {account_id} vào {self.blocked_accounts_file} (vĩnh viễn)")
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi lưu blocked account: {e}")
    
    def _save_max_job_account(self, account_id):
        """
        Lưu tài khoản đã max job vào file (tạm thời - chỉ trong ngày)
        Args:
            account_id: ID tài khoản dạng "Y_265", "Y_372", etc.
        """
        try:
            if account_id in self.max_job_accounts:
                self.log_fn(f"   ℹ️ {account_id} đã có trong danh sách max job")
                return
            
            self.max_job_accounts.add(account_id)
            
            with open(self.max_job_accounts_file, 'a', encoding='utf-8') as f:
                f.write(f"{account_id}\n")
            
            self.log_fn(f"   ✓ Đã lưu {account_id} vào {self.max_job_accounts_file} (hôm nay)")
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi lưu max job account: {e}")
    
    def get_account_stt_from_position(self, y):
        """
        Lấy STT tài khoản dựa trên vị trí Y
        
        CÁCH MỚI: Dùng khoảng Y để xác định STT
        
        Dựa trên hình ảnh:
        - Acc 1 (Hà Trần):    y ≈ 200-250
        - Acc 2 (Trần Ánh):   y ≈ 280-350
        - Acc 3 (Kiếm Tiền):  y ≈ 380-450
        - Acc 4 (Người Mới):  y ≈ 490-560
        - Acc 5 (Ối Chị):     y ≈ 600-670
        
        Args:
            y: Tọa độ Y của tài khoản
        Returns: STT tài khoản (1, 2, 3, ...)
        """
        # Định nghĩa khoảng Y cho từng STT
        # Format: (y_min, y_max, stt)
        y_ranges = [
            (150, 260, 1),   # Acc 1
            (261, 370, 2),   # Acc 2
            (371, 480, 3),   # Acc 3
            (481, 590, 4),   # Acc 4
            (591, 700, 5),   # Acc 5
        ]
        
        # Tìm STT dựa trên khoảng Y
        for y_min, y_max, stt in y_ranges:
            if y_min <= y <= y_max:
                self.log_fn(f"      [DEBUG] y={y} → STT {stt} (khoảng {y_min}-{y_max})")
                return stt
        
        # Fallback: Tính theo công thức (nếu nằm ngoài khoảng)
        first_acc_y = 218
        acc_spacing = 100
        stt = round((y - first_acc_y) / acc_spacing) + 1
        
        if stt < 1:
            stt = 1
        elif stt > 5:
            stt = 5
        
        self.log_fn(f"      [DEBUG] y={y} → STT {stt} (fallback)")
        return stt
    
    def get_account_id_from_position(self, x, y):
        """
        Lấy ID tài khoản từ vị trí (dùng tọa độ X,Y)
        
        CHIẾN LƯỢC:
        - Lưu cả tọa độ X,Y làm ID (chính xác nhất)
        - Format: "211_205", "273_265", "274_372"
        - Giống format ADB tap: "ADB tap success at (211, 205)"
        
        Args:
            x, y: Tọa độ trung tâm tài khoản
        Returns: ID tài khoản dạng "X_Y"
        """
        try:
            account_id = f"{x}_{y}"
            self.log_fn(f"      ✓ Tài khoản tại ({x}, {y}) → ID: '{account_id}'")
            return account_id
            
        except Exception as e:
            self.log_fn(f"      ⚠️ Lỗi khi lấy ID: {e}")
            return None
    
    def get_current_account_id(self):
        """
        Lấy ID tài khoản hiện tại (dựa trên tọa độ X,Y)
        
        Returns: ID tài khoản dạng "211_205", "273_265", etc.
        """
        try:
            # Phát hiện vị trí tài khoản hiện tại
            pos = self.detect_current_account_position_in_list()
            
            if pos:
                x, y = pos
                account_id = f"{x}_{y}"
                self.log_fn(f"   ✓ Tài khoản hiện tại: {account_id} (tọa độ: {x}, {y})")
                return account_id
            
            # Fallback: Không phát hiện được
            self.log_fn(f"   ⚠️ Không phát hiện được tài khoản hiện tại")
            return None
            
        except Exception as e:
            self.log_fn(f"   ⚠️ Lỗi khi lấy ID tài khoản: {e}")
            return None
    
    def handle_blocked_account(self):
        """
        Xử lý khi tài khoản bị block (lưu vĩnh viễn)
        Returns: True nếu xử lý thành công
        """
        try:
            self.log_fn("🔒 Xử lý tài khoản bị block...")
            
            # Dùng ID đã lưu từ lúc khởi động (nhanh hơn, chính xác hơn)
            account_id = self.current_account_name
            
            if not account_id:
                # Fallback: Mở menu và tìm tài khoản đầu tiên
                self.log_fn("   ⚠️ Chưa có ID tài khoản, thử phát hiện từ danh sách...")
                
                # Mở menu chọn tài khoản
                if self.open_account_selector():
                    time.sleep(2.0)  # Đợi menu hiện ra
                    
                    # Tìm tài khoản đầu tiên (tài khoản hiện tại)
                    all_accounts = self.find_all_accounts()
                    
                    if all_accounts:
                        # Sắp xếp theo Y
                        all_accounts.sort(key=lambda a: a[1])
                        
                        # Tài khoản đầu tiên
                        x, y, score = all_accounts[0]
                        account_id = f"{x}_{y}"
                        
                        self.log_fn(f"   ✓ Phát hiện tài khoản: {account_id}")
            
            if not account_id:
                # Nếu vẫn không phát hiện được, dùng 0_0 (giả định)
                account_id = "0_0"
                self.log_fn(f"   ⚠️ Không xác định được, dùng mặc định: {account_id}")
            else:
                self.log_fn(f"   ✓ Tài khoản: {account_id}")
            
            # Lưu vào file blocked (vĩnh viễn)
            self.log_fn(f"   [DEBUG] Đang lưu '{account_id}' vào file...")
            self._save_blocked_account(account_id)
            self.log_fn(f"   [DEBUG] Đã lưu xong!")
            
            # Click OK để đóng popup
            self.log_fn("   [1/2] Đóng popup...")
            self.click_ok_button()
            time.sleep(1.0)
            
            # Chuyển sang tài khoản khác
            self.log_fn("   [2/2] Chuyển sang tài khoản khác...")
            return self.switch_account(skip_ok_button=True)
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi xử lý blocked account: {e}")
            import traceback
            self.log_fn(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def handle_max_job_account(self):
        """
        Xử lý khi tài khoản đã max job (lưu tạm thời - chỉ trong ngày)
        Returns: True nếu xử lý thành công
        """
        try:
            self.log_fn("🚫 Xử lý tài khoản đã max job...")
            
            # Dùng ID đã lưu từ lúc khởi động (nhanh hơn, chính xác hơn)
            account_id = self.current_account_name
            
            if not account_id:
                # Fallback: Mở menu và tìm tài khoản đầu tiên
                self.log_fn("   ⚠️ Chưa có ID tài khoản, thử phát hiện từ danh sách...")
                
                # Mở menu chọn tài khoản
                if self.open_account_selector():
                    time.sleep(2.0)  # Đợi menu hiện ra
                    
                    # Tìm tài khoản đầu tiên (tài khoản hiện tại)
                    all_accounts = self.find_all_accounts()
                    
                    if all_accounts:
                        # Sắp xếp theo Y
                        all_accounts.sort(key=lambda a: a[1])
                        
                        # Tài khoản đầu tiên
                        x, y, score = all_accounts[0]
                        account_id = f"{x}_{y}"
                        
                        self.log_fn(f"   ✓ Phát hiện tài khoản: {account_id}")
            
            if not account_id:
                # Nếu vẫn không phát hiện được, dùng 0_0 (giả định)
                account_id = "0_0"
                self.log_fn(f"   ⚠️ Không xác định được, dùng mặc định: {account_id}")
            else:
                self.log_fn(f"   ✓ Tài khoản: {account_id}")
            
            # Lưu vào file max_job (chỉ trong ngày)
            self.log_fn(f"   [DEBUG] Đang lưu '{account_id}' vào file...")
            self._save_max_job_account(account_id)
            self.log_fn(f"   [DEBUG] Đã lưu xong!")
            
            return True
            
        except Exception as e:
            self.log_fn(f"⚠️ Lỗi khi xử lý max job account: {e}")
            import traceback
            self.log_fn(f"   Traceback: {traceback.format_exc()}")
            return False

