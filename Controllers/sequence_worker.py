#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sequence_worker.py - Worker chính xử lý sequence các jobs
"""
import os
import time
import random
import threading
import webbrowser
import pyautogui
import gc  # Garbage collector để dọn dẹp bộ nhớ

from Controllers.ok_watcher import OkWatcher, ok_watcher_suspend, sequence_worker_pause
from Controllers.job_detector import JobDetector
from Utils.navigation import press_back_method
from Utils.image_utils import load_gray, locate_template, locate_template_multiscale, set_adb_mode as image_set_adb_mode, screenshot_gray
from Utils.window_utils import click_at, get_ldplayer_window, attempt_scroll_or_drag, set_adb_mode as window_set_adb_mode
from Utils.adb_utils import get_adb_controller, init_adb_connection
from Models.coin_tracker import get_coin_tracker, extract_coins_from_text
from Models.config import get_template_path
from Utils.ocr_utils import extract_text_from_image, check_ocr_available
from Controllers.account_switcher import AccountSwitcher

try:
    import pygetwindow as gw
except Exception:
    gw = None

class SequenceWorker:
    """Worker chính để xử lý sequence automation"""
    
    def __init__(self, ui):
        self.ui = ui
        self._stop = threading.Event()
        self.thread = None
        self.ok_watcher = None
        self.no_job_cycles = 0
        self.no_job_threshold = 10
        self.jobs = []
        self.templates = {}
        self.params = {}
        
        # Memory management - Dựa vào số vòng thay vì số job
        self.cycle_count = 0  # Đếm số vòng đã chạy
        self.gc_interval = 100  # Chạy GC sau mỗi 100 vòng
        self.restart_interval = 800  # Restart LDPlayer sau 800 vòng
        
        # Account switcher
        self.account_switcher = None

    def log(self, msg):
        """Log message với timestamp"""
        ts = time.strftime("%H:%M:%S")
        try:
            self.ui.append_log(f"[{ts}] {msg}")
        except Exception:
            print(f"[{ts}] {msg}")

    def start(self, jobs, templates, params):
        """Khởi động worker"""
        self.jobs = jobs
        self.templates = templates
        self.params = params
        self._stop.clear()
        self.no_job_cycles = 0
        
        # Kiểm tra và khởi tạo ADB nếu được bật
        use_adb = self.ui.use_adb_var.get() if hasattr(self.ui, 'use_adb_var') else False
        if use_adb:
            adb_path = self.ui.adb_path_entry.get().strip() if hasattr(self.ui, 'adb_path_entry') else "adb"
            adb_port = int(self.ui.adb_port_entry.get().strip()) if hasattr(self.ui, 'adb_port_entry') and self.ui.adb_port_entry.get().strip().isdigit() else 5555
            adb_device = self.ui.adb_device_combo.get().strip() if hasattr(self.ui, 'adb_device_combo') else ''
            
            self.log(f"🎮 Chế độ ADB được bật - Kết nối tới LDPlayer...")
            
            # Khởi tạo controller
            from Utils.adb_utils import ADBController
            controller = ADBController(adb_path=adb_path)
            
            # Kết nối với device_id nếu có
            if controller.connect(port=adb_port, device_id=adb_device if adb_device else None):
                window_set_adb_mode(True, controller)
                image_set_adb_mode(True, controller)
                self.log(f"✓ Đã kết nối ADB - Device: {controller.device_id}")
                self.log(f"✓ Sử dụng chuột ảo trong LDPlayer")
                
                # Lấy kích thước màn hình
                screen_size = controller.get_screen_size()
                if screen_size:
                    self.log(f"✓ Kích thước màn hình LDPlayer: {screen_size[0]}x{screen_size[1]}")
            else:
                self.log("⚠ Không thể kết nối ADB - Chuyển về chế độ thường")
                window_set_adb_mode(False)
                image_set_adb_mode(False)
        else:
            self.log("ℹ️ Chế độ thường (toàn màn hình)")
            window_set_adb_mode(False)
            image_set_adb_mode(False)
        
        # Khởi tạo account_switcher trước
        self.account_switcher = AccountSwitcher(self.templates, self.params, self.log)
        
        # Khởi tạo EasyOCR (tốt cho tiếng Việt)
        self.log("=" * 50)
        self.log("🔧 Khởi tạo OCR...")
        try:
            from Utils.ocr_utils import init_easyocr, get_ocr_method
            if init_easyocr():
                self.log(f"✓ Sử dụng EasyOCR (tốt cho tiếng Việt)")
            else:
                method = get_ocr_method()
                self.log(f"ℹ️ Sử dụng {method}")
        except Exception as e:
            self.log(f"⚠️ Lỗi khởi tạo OCR: {e}")
        
        # QUAN TRỌNG: Đọc tên tài khoản hiện tại trước khi bắt đầu
        self.account_switcher.initialize_current_account()
        self.log("=" * 50)
        
        # Khởi động OkWatcher với account_switcher
        def _get_templates(): return self.templates
        def _get_params(): return self.params
        self.ok_watcher = OkWatcher(_get_templates, _get_params, log_fn=self.log, ui=self.ui, account_switcher=self.account_switcher)
        self.ok_watcher.start()
        
        # Khởi động worker thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Dừng worker"""
        try:
            if self.ok_watcher:
                self.ok_watcher.stop()
        except Exception:
            pass
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=1.0)

    def _should_stop(self):
        """Kiểm tra xem có nên dừng không"""
        # Kiểm tra flag dừng thông thường
        if self._stop.is_set():
            return True
        
        # Kiểm tra flag từ account_switcher (không còn tài khoản hợp lệ)
        if self.account_switcher and hasattr(self.account_switcher, 'should_stop_tool'):
            if self.account_switcher.should_stop_tool:
                self.log("🛑 Dừng tool vì không còn tài khoản hợp lệ")
                self._stop.set()  # Set flag để dừng
                return True
        
        return False
    
    def _cleanup_memory(self):
        """Dọn dẹp bộ nhớ và cache để tránh memory leak"""
        try:
            self.log(f"🧹 Dọn dẹp bộ nhớ và cache (đã chạy {self.cycle_count} vòng)...")
            
            # Force garbage collection
            collected = gc.collect()
            self.log(f"   ✓ Đã thu hồi {collected} objects")
            
            # Clear template cache nếu có
            if hasattr(self, 'template_cache'):
                self.template_cache.clear()
                self.log(f"   ✓ Template cache đã được xóa")
            
            # Clear OpenCV cache
            try:
                import cv2
                # Clear internal caches
                cv2.setUseOptimized(False)
                cv2.setUseOptimized(True)
                self.log(f"   ✓ OpenCV cache đã được reset")
            except Exception:
                pass
            
            # Clear PIL/Pillow cache
            try:
                from PIL import Image
                Image.MAX_IMAGE_PIXELS = None  # Reset limit
                self.log(f"   ✓ PIL cache đã được reset")
            except Exception:
                pass
            
            # Clear screenshot cache (nếu có)
            try:
                from Utils.image_utils import clear_screenshot_cache
                clear_screenshot_cache()
                self.log(f"   ✓ Screenshot cache đã được xóa")
            except Exception:
                pass
            
            self.log(f"   ✅ Hoàn tất dọn dẹp cache và memory")
            
        except Exception as e:
            self.log(f"⚠️ Lỗi khi cleanup memory: {e}")
    
    def _auto_restart_ldplayer(self):
        """Tự động restart LDPlayer sau 800 vòng"""
        try:
            self.log(f"🔄 Đã chạy {self.cycle_count} vòng - Tự động restart LDPlayer...")
            self.log(f"   ⏳ Quá trình này mất ~40 giây, vui lòng đợi...")
            
            from Utils.ldplayer_manager import LDPlayerManager
            manager = LDPlayerManager()
            
            # Restart LDPlayer
            success = manager.restart_ldplayer(index=0)
            
            if success:
                self.log(f"   ✓ LDPlayer đã restart thành công!")
                
                # Đợi lâu hơn để LDPlayer khởi động hoàn toàn
                self.log(f"   ⏳ Đợi LDPlayer khởi động hoàn toàn (20 giây)...")
                time.sleep(20)
                
                # Mở app Golike
                self.log(f"   📱 Đang mở app Golike...")
                app_opened = self._open_golike_app()
                
                if app_opened:
                    # Đợi app load hoàn toàn
                    self.log(f"   ⏳ Đợi app Golike load (10 giây)...")
                    time.sleep(10)
                    
                    # Reset navigation để về đúng vị trí làm việc
                    self.log(f"   🧭 Đang vào màn hình 'Kiếm thưởng'...")
                    self._reset_navigation()
                    
                    self.log(f"   ✅ Hoàn tất! Bot tiếp tục chạy...")
                else:
                    self.log(f"   ⚠️ Không mở được app - Bot tiếp tục chạy")
                
            else:
                self.log(f"   ⚠️ Restart LDPlayer thất bại - Bot tiếp tục chạy")
            
        except Exception as e:
            self.log(f"⚠️ Lỗi khi auto restart LDPlayer: {e}")
            self.log(f"   Bot sẽ tiếp tục chạy bình thường")
    
    def _open_golike_app(self):
        """
        Mở app Golike sau khi restart LDPlayer
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            from Utils.window_utils import is_adb_mode, set_adb_mode as window_set_adb_mode
            from Utils.image_utils import set_adb_mode as image_set_adb_mode
            from Utils.adb_utils import ADBController, get_adb_controller
            
            if not is_adb_mode():
                self.log(f"      ⚠️ Không ở ADB mode - Bỏ qua mở app")
                return False
            
            # Kết nối lại ADB (sau restart phải kết nối lại)
            self.log(f"      🔌 Kết nối lại ADB...")
            
            # Lấy thông tin ADB từ UI
            adb_path = "adb"
            adb_port = 5555
            if hasattr(self.ui, 'adb_path_entry'):
                adb_path = self.ui.adb_path_entry.get().strip() or "adb"
            if hasattr(self.ui, 'adb_port_entry'):
                try:
                    adb_port = int(self.ui.adb_port_entry.get().strip())
                except:
                    adb_port = 5555
            
            # Tạo controller mới và kết nối
            controller = ADBController(adb_path=adb_path)
            
            # Thử kết nối nhiều lần
            max_retries = 5
            connected = False
            
            for attempt in range(max_retries):
                if controller.connect(port=adb_port):
                    self.log(f"      ✓ Đã kết nối ADB - Device: {controller.device_id}")
                    
                    # CẬP NHẬT controller cho window_utils và image_utils
                    window_set_adb_mode(True, controller)
                    image_set_adb_mode(True, controller)
                    
                    connected = True
                    break
                else:
                    if attempt < max_retries - 1:
                        self.log(f"      ⏳ Thử lại kết nối ADB ({attempt + 1}/{max_retries})...")
                        time.sleep(5)
            
            if not connected:
                self.log(f"      ⚠️ Không thể kết nối ADB sau {max_retries} lần thử")
                return False
            
            # Đợi thêm để LDPlayer ổn định hoàn toàn
            self.log(f"      ⏳ Đợi LDPlayer ổn định (5 giây)...")
            time.sleep(5)
            
            # Nhấn Home để về màn hình chính (đảm bảo không có app nào đang chạy)
            self.log(f"      🏠 Nhấn Home button để về màn hình chính...")
            controller.press_home()
            time.sleep(3)
            
            # Mở app Golike bằng package name
            golike_package = self.params.get('golike_package', 'com.golike.app')
            self.log(f"      📱 Mở app Golike ({golike_package})...")
            success = controller.open_app(golike_package)
            
            if success:
                self.log(f"      ✓ Đã gửi lệnh mở app")
                
                # Đợi app load
                self.log(f"      ⏳ Đợi app load (8 giây)...")
                time.sleep(8)
                
                # Nhấn Space để tắt popup (nếu có)
                self.log(f"      ⏎ Nhấn Space để tắt popup...")
                controller.press_key("KEYCODE_SPACE")
                time.sleep(1)
                
                return True
            else:
                # Fallback: Tìm và click icon Golike
                self.log(f"      ⚠️ Không mở được bằng package name")
                self.log(f"      🔍 Thử tìm và click icon Golike trên Home...")
                
                if self._click_golike_icon():
                    self.log(f"      ✓ Đã click icon Golike")
                    
                    # Đợi app load
                    time.sleep(8)
                    
                    # Nhấn Space để tắt popup
                    self.log(f"      ⏎ Nhấn Space để tắt popup...")
                    controller.press_key("KEYCODE_SPACE")
                    time.sleep(1)
                    
                    return True
                else:
                    self.log(f"      ⚠️ Không tìm thấy icon Golike")
                    return False
                
        except Exception as e:
            self.log(f"      ⚠️ Lỗi khi mở app Golike: {e}")
            import traceback
            self.log(f"      Traceback: {traceback.format_exc()}")
            return False
    
    def _click_golike_icon(self):
        """
        Tìm và click icon Golike trên màn hình Home
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            from Utils.image_utils import load_gray, locate_template_multiscale
            from Utils.window_utils import click_at
            
            # Tìm template golike_icon
            golike_keys = ['golike_icon', 'ld_golike_icon', 'golike']
            
            for key in golike_keys:
                if key in self.templates:
                    template_path = get_template_path(self.templates[key])
                    try:
                        tmpl = load_gray(template_path)
                        
                        # Tìm với confidence thấp hơn
                        found = locate_template_multiscale(
                            tmpl, confidence=0.75, timeout=5.0,
                            step=0.08, region=None
                        )
                        
                        if found:
                            x, y, score = found
                            self.log(f"         ✓ Tìm thấy icon '{key}' tại ({x}, {y}) score={score:.2f}")
                            click_at(x, y)
                            time.sleep(0.5)
                            return True
                    except Exception as e:
                        self.log(f"         ⚠️ Lỗi khi tìm '{key}': {e}")
            
            return False
            
        except Exception as e:
            self.log(f"         ⚠️ Lỗi khi click icon Golike: {e}")
            return False


    def _check_earn_page(self):
        """
        Kiểm tra xem có đang ở trang 'Kiếm thưởng' (trang load job) không
        Returns: True nếu đang ở đúng trang, False nếu không
        """
        try:
            # Tìm các template đặc trưng của trang Kiếm thưởng
            earn_page_keys = ['earn_page_header', 'kiem_thuong_header', 'danh_sach_cong_viec']
            
            for key in earn_page_keys:
                if key in self.templates:
                    template_path = get_template_path(self.templates[key])
                    try:
                        tmpl = load_gray(template_path)
                        found = locate_template(
                            tmpl, confidence=0.80, timeout=1.0,
                            step=0.08, region=None
                        )
                        
                        if found:
                            return True
                    except Exception:
                        pass
            
            # Nếu không có template riêng, kiểm tra bằng cách tìm job icon
            # Nếu tìm thấy job icon thì có thể đang ở đúng trang
            return None  # Không chắc chắn
            
        except Exception as e:
            self.log(f"⚠️ Lỗi khi kiểm tra trang Kiếm thưởng: {e}")
            return None

    def _run(self):
        """Main loop của worker"""
        job_count = len(self.jobs) if self.jobs else 0
        self.log(f"▶ Bắt đầu chạy liên tục. Dừng bằng nút 'Dừng' trong GUI hoặc Ctrl+C.")
        
        if job_count == 0:
            self.log("⚠ Không có jobs (app sẽ chạy vòng với job = None).")
        
        cycle = 0
        while not self._should_stop():
            # Kiểm tra xem có bị pause không (OkWatcher đang xử lý popup)
            if sequence_worker_pause.is_set():
                time.sleep(0.2)
                continue
            
            cycle += 1
            self.cycle_count += 1  # Tăng cycle counter
            iterable = self.jobs if self.jobs else [None]
            
            # Kiểm tra GC sau mỗi 100 vòng
            if self.cycle_count % self.gc_interval == 0:
                self._cleanup_memory()
            
            # Kiểm tra restart LDPlayer sau mỗi 800 vòng
            if self.cycle_count % self.restart_interval == 0:
                self._auto_restart_ldplayer()
            
            # Kiểm tra trang Kiếm thưởng mỗi 10 vòng
            if cycle % 10 == 1:  # Vòng 1, 11, 21, 31...
                on_earn_page = self._check_earn_page()
                if on_earn_page is False:
                    self.log("⚠️ Không ở trang 'Kiếm thưởng' - Đang reset navigation...")
                    try:
                        self._reset_navigation()
                    except Exception as e:
                        self.log(f"⚠️ Lỗi khi reset navigation: {e}")
            
            for idx, job in enumerate(iterable, start=1):
                # Kiểm tra pause trong vòng lặp job
                if sequence_worker_pause.is_set():
                    self.log("⏸️ Thread tìm job đã tạm dừng (OkWatcher đang xử lý popup)")
                    while sequence_worker_pause.is_set() and not self._should_stop():
                        time.sleep(0.2)
                    self.log("▶️ Thread tìm job tiếp tục...")
                
                if self._should_stop():
                    break
                
                self.log(f"--- Vòng {cycle} - Job [{idx}/{len(iterable)}] ---")
                self._process_single_job(job)
        
        self.log("⏹ Worker đã dừng.")

    def _process_single_job(self, job):
        """Xử lý một job đơn lẻ"""
        # Tăng counter job attempts
        if hasattr(self.ui, 'increment_job_attempts'):
            try:
                self.ui.increment_job_attempts()
            except Exception as e:
                self.log(f"⚠️ Lỗi khi cập nhật job attempts counter: {e}")
        
        # Mở URL nếu có
        if job:
            try:
                webbrowser.open(job)
                self.log("Đã mở URL job trên trình duyệt")
                time.sleep(random.uniform(1.6, 2.6))
            except Exception as e:
                self.log(f"Không thể mở URL: {e}")
        
        # Tìm và click job icon
        job_detector = JobDetector(self.templates, self.params, self.log)
        found_job_icon = None
        
        try:
            result = job_detector.find_and_click_job_icons(
                retries_per_template=1, 
                timeout_per_try=self.params.get('timeout_job')
            )
            if result is not None:
                found_job_icon = result
            else:
                self.log("Không tìm thấy bất kỳ icon nhận job nào -> bỏ qua job này")
        except Exception as e:
            self.log(f"Lỗi khi tìm nhiều job_icon: {e}")
        
        # Cập nhật no_job counter
        if not found_job_icon:
            self.no_job_cycles += 1
            self.log(f"(Info) No-job cycles: {self.no_job_cycles}/{self.no_job_threshold}")
        else:
            self.no_job_cycles = 0
        
        # Reset navigation nếu cần
        if self.no_job_cycles >= self.no_job_threshold:
            try:
                self._reset_navigation()
            except Exception as e:
                self.log(f"Lỗi khi reset navigation: {e}")
        
        if not found_job_icon:
            time.sleep(random.uniform(
                self.params.get('min_between', 0.5), 
                self.params.get('max_between', 0.8)
            ))
            return
        
        if self._should_stop():
            return
        
        # Click copy button nếu có
        self._try_click_copy_button(job_detector)
        
        # Thực hiện job với retry (tối đa 2 lần retry nếu fail)
        self._execute_job_with_retry()

    def _execute_job_with_retry(self):
        """
        Thực hiện job với retry logic:
        - Lần 1: Thực hiện bình thường
        - Nếu fail: Retry lần 2 (từ bước click FB)
        - Nếu vẫn fail: Retry lần 3 (từ bước click FB)
        - Sau 3 lần vẫn fail: Báo lỗi
        """
        max_retries = 2  # Tổng cộng 3 lần (1 lần đầu + 2 retry)
        
        for attempt in range(max_retries + 1):
            if self._should_stop():
                return
            
            if attempt > 0:
                self.log(f"🔄 Retry lần {attempt}/{max_retries} (job bị lỗi)")
                time.sleep(1.0)  # Đợi trước khi retry
            
            # Click FB icon nếu có
            self._try_click_fb_icon()
            
            if self._should_stop():
                return
            
            # Thực hiện BACK
            self._perform_back_action()
            
            if self._should_stop():
                return
            
            # Kiểm tra kết quả
            result = self._check_job_result_with_status()
            
            if result == 'success':
                # Job thành công, thoát
                self.log(f"✅ Job hoàn thành thành công" + (f" (sau {attempt} lần retry)" if attempt > 0 else ""))
                
                # Tăng counter job hoàn thành
                if hasattr(self.ui, 'increment_completed_jobs'):
                    try:
                        self.ui.increment_completed_jobs()
                    except Exception as e:
                        self.log(f"⚠️ Lỗi khi cập nhật counter: {e}")
                
                return
            elif result == 'fail':
                # Job thất bại
                if attempt < max_retries:
                    self.log(f"❌ Job thất bại - Sẽ retry...")
                    continue  # Retry
                else:
                    # Đã retry đủ số lần, báo lỗi
                    self.log(f"❌ Job thất bại sau {max_retries + 1} lần thử - Báo lỗi")
                    self._handle_final_fail()
                    return
            else:
                # Unknown (không phát hiện gì)
                self.log(f"⚠️ Không phát hiện kết quả rõ ràng")
                if attempt < max_retries:
                    self.log(f"🔄 Sẽ retry để chắc chắn...")
                    continue
                else:
                    self.log(f"⚠️ Không rõ kết quả sau {max_retries + 1} lần - Bỏ qua job")
                    return
    
    def _try_click_copy_button(self, job_detector):
        """Thử click nút copy nếu có"""
        copy_keys = ['copy_button', 'click_to_copy', 'btn_copy', 'copy']
        try:
            clicked_copy = job_detector.try_click_optional_templates(
                copy_keys, timeout_per_try=0.3, retries=2, conf_key='conf_job'
            )
            if clicked_copy:
                self.log("Đã click nút Copy (nếu có).")
            else:
                self.log("Không tìm thấy nút Copy (bỏ qua).")
        except Exception as e:
            self.log(f"Lỗi khi xử lý optional copy button: {e}")

    def _try_click_fb_icon(self):
        """Thử click FB icon nếu có"""
        if self.templates.get('fb_icon'):
            try:
                tmpl = load_gray(get_template_path(self.templates['fb_icon']))
                res = locate_template(
                    tmpl, 
                    confidence=self.params['conf_fb'], 
                    timeout=self.params['timeout_fb']
                )
                if res is not None:
                    x, y, _ = res
                    self.log("Tìm thấy icon Facebook -> click (mở FB)")
                    click_at(x, y)
                    time.sleep(random.uniform(1.6, 2.8))
                else:
                    self.log("Không thấy icon FB (có thể không cần mở FB)")
            except Exception as e:
                self.log(f"Lỗi fb_icon: {e}")

    def _perform_back_action(self):
        """Thực hiện hành động BACK"""
        ok = press_back_method(
            self.params['back_method'], 
            self.params.get('back_coord'), 
            templates=self.templates, 
            params=self.params
        )
        self.log(f"Đã thực hiện hành động BACK -> {'OK' if ok else 'Thất bại'}")
        time.sleep(random.uniform(1.6, 2.6))

    def _check_job_result_with_status(self):
        """
        Kiểm tra kết quả job (complete hoặc fail)
        Returns: 'success', 'fail', hoặc 'unknown'
        """
        # Kiểm tra complete
        success_detected = self._check_complete_icon()
        
        if success_detected:
            wait_after = max(0.8, float(self.params.get('timeout_complete', 2.0)))
            time.sleep(wait_after)
            if self.params.get('close_tab_after'):
                try:
                    pyautogui.hotkey('ctrl', 'w')
                except Exception:
                    pass
            time.sleep(random.uniform(
                self.params['min_between'], 
                self.params['max_between']
            ))
            return 'success'
        
        # Kiểm tra fail
        fail_detected = self._check_fail_icon_only()
        
        if fail_detected:
            return 'fail'
        
        # Không phát hiện gì
        self.log("Không phát hiện Hoàn thành hoặc Thất bại -> UNKNOWN")
        return 'unknown'
    
    def _handle_final_fail(self):
        """Xử lý khi job thất bại sau tất cả retry"""
        self.log("🔴 Bắt đầu xử lý báo lỗi...")
        ok_watcher_suspend.set()
        try:
            self._handle_fail_sequence()
        except Exception as e:
            self.log(f"Lỗi khi xử lý fail sequence: {e}")
        finally:
            ok_watcher_suspend.clear()
        
        if self.params.get('close_tab_after'):
            try:
                pyautogui.hotkey('ctrl', 'w')
            except Exception:
                pass
        
        time.sleep(random.uniform(
            self.params['min_between'], 
            self.params['max_between']
        ))

    def _check_complete_icon(self):
        """Kiểm tra complete icon"""
        if not self.templates.get('complete_icon'):
            return False
        
        try:
            tmpl = load_gray(get_template_path(self.templates['complete_icon']))
            res = locate_template(
                tmpl, 
                confidence=self.params['conf_complete'], 
                timeout=self.params['timeout_complete']
            )
            
            if res is not None:
                self.log("✓ Phát hiện icon Hoàn thành -> SUCCESS")
                ok_watcher_suspend.set()
                try:
                    if self.params.get('click_complete', True):
                        click_at(res[0], res[1])
                        time.sleep(random.uniform(0.2, 0.5))
                        
                        # OCR xu sẽ được xử lý bởi OkWatcher khi tìm thấy nút OK
                        self.log("✓ Đã click Hoàn thành - Đợi nút OK để đọc xu...")
                    else:
                        self.log("click_complete disabled; không click COMPLETE.")
                except Exception as e:
                    self.log(f"Lỗi khi click COMPLETE: {e}")
                finally:
                    ok_watcher_suspend.clear()
                return True
        except Exception as e:
            self.log(f"Lỗi complete_icon: {e}")
        
        return False

    def _check_fail_icon_only(self):
        """
        Chỉ kiểm tra fail icon (không xử lý)
        Returns: True nếu phát hiện fail, False nếu không
        """
        if not self.templates.get('fail_icon'):
            return False
        
        try:
            tmpl = load_gray(get_template_path(self.templates['fail_icon']))
            res = locate_template(
                tmpl, 
                confidence=self.params['conf_fail'], 
                timeout=self.params['timeout_fail']
            )
            
            if res is not None:
                self.log("❌ Phát hiện icon Thất bại")
                return True
        except Exception as e:
            self.log(f"Lỗi fail_icon: {e}")
        
        return False

    def _handle_fail_sequence(self):
        """Xử lý sequence khi phát hiện fail"""
        # Click OK trước
        ok_path = self.templates.get('ok_button')
        if ok_path and os.path.exists(ok_path):
            try:
                otmpl = load_gray(ok_path)
                ok_res = locate_template(
                    otmpl, 
                    confidence=self.params.get('conf_okbtn', 0.85), 
                    timeout=1.2
                )
                if ok_res is not None:
                    self.log("SequenceWorker: click OK (non-complete fail path)")
                    click_at(ok_res[0], ok_res[1])
                    time.sleep(0.6)
            except Exception as e:
                self.log(f"Lỗi khi tìm/ấn ok_button lúc fail (non-complete): {e}")
        
        # Tìm fail button
        fb_path = self.templates.get('fail_button')
        found_fb = False
        
        if fb_path and os.path.exists(fb_path):
            for i in range(3):
                if self._should_stop():
                    break
                try:
                    ft2 = load_gray(fb_path)
                    fb_res = locate_template(
                        ft2, 
                        confidence=self.params.get('conf_failbtn', 0.85), 
                        timeout=1
                    )
                    if fb_res is not None:
                        self.log("SequenceWorker: tìm thấy nút báo lỗi -> click (non-complete)")
                        click_at(fb_res[0], fb_res[1])
                        time.sleep(0.6)
                        found_fb = True
                        break
                except Exception as e:
                    self.log(f"Lỗi tìm fail_button (non-complete): {e}")
                
                attempt_scroll_or_drag(force=True)
                time.sleep(0.45)
        
        if found_fb:
            # Cuộn và tìm confirm
            for _ in range(3):
                if self._should_stop():
                    break
                attempt_scroll_or_drag(force=True)
                time.sleep(0.25)
            
            # Click confirm
            confirm_path = self.templates.get('confirm_button')
            confirmed = False
            
            if confirm_path and os.path.exists(confirm_path):
                try:
                    ctmpl = load_gray(confirm_path)
                    cres_confirm = locate_template(
                        ctmpl, 
                        confidence=self.params.get('conf_okbtn', 0.85), 
                        timeout=2
                    )
                    if cres_confirm is not None:
                        self.log("SequenceWorker: click Confirm (non-complete)")
                        click_at(cres_confirm[0], cres_confirm[1])
                        time.sleep(0.6)
                        confirmed = True
                except Exception as e:
                    self.log(f"Lỗi tìm confirm_button (non-complete): {e}")
            
            # Fallback OK
            if not confirmed and ok_path and os.path.exists(ok_path):
                try:
                    otmpl2 = load_gray(ok_path)
                    ok_res2 = locate_template(
                        otmpl2, 
                        confidence=self.params.get('conf_okbtn', 0.85), 
                        timeout=2
                    )
                    if ok_res2 is not None:
                        self.log("SequenceWorker: fallback click OK (non-complete)")
                        click_at(ok_res2[0], ok_res2[1])
                        time.sleep(0.6)
                except Exception as e:
                    self.log(f"Lỗi fallback ok_button (non-complete): {e}")
        else:
            self.log("SequenceWorker: không tìm thấy fail_button (non-complete)")

    def _reset_navigation(self):
        """Reset điều hướng khi không tìm thấy job quá lâu"""
        from Controllers.reset_navigation import ResetNavigation
        reset_nav = ResetNavigation(self.templates, self.params, self.log, self._should_stop)
        reset_nav.perform_reset()
        self.no_job_cycles = 0


