#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ok_watcher.py - Thread giám sát và xử lý nút OK/Fail
"""
import os
import time
import threading
from Utils.image_utils import load_gray, locate_template
from Utils.window_utils import click_at, attempt_scroll_or_drag

# Event để tạm dừng watcher khi cần
ok_watcher_suspend = threading.Event()

# Event để tạm dừng sequence_worker khi OkWatcher đang xử lý popup
sequence_worker_pause = threading.Event()

class OkWatcher:
    """
    Thread giám sát liên tục để tự động click OK
    Kiểm tra fail icon trước khi click OK
    OCR để đọc số xu khi tìm thấy OK
    """
    def __init__(self, templates_getter, params_getter, log_fn=None, ui=None, account_switcher=None):
        self.templates_getter = templates_getter
        self.params_getter = params_getter
        self.log_fn = log_fn or (lambda m: None)
        self.ui = ui
        self.account_switcher = account_switcher
        self._stop = threading.Event()
        self.thread = None

    def start(self):
        """Khởi động watcher thread"""
        if self.thread and self.thread.is_alive():
            return
        self._stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.log_fn("OkWatcher: started")

    def stop(self):
        """Dừng watcher thread"""
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=1.0)
        self.log_fn("OkWatcher: stopped")

    def _run(self):
        """Main loop của watcher"""
        last_click_ts = 0
        
        while not self._stop.is_set():
            if ok_watcher_suspend.is_set():
                time.sleep(0.1)
                continue
            
            try:
                templates = self.templates_getter() or {}
                params = self.params_getter() or {}
                ok_path = templates.get('ok_button')
                
                if ok_path and os.path.exists(ok_path):
                    self._check_and_click_ok(ok_path, templates, params, last_click_ts)
                else:
                    time.sleep(0.5)
            except Exception as e:
                try:
                    self.log_fn(f"OkWatcher unexpected error: {e}")
                except:
                    pass
                time.sleep(0.4)

    def _check_and_click_ok(self, ok_path, templates, params, last_click_ts):
        """Kiểm tra và click nút OK"""
        try:
            otmpl = load_gray(ok_path)
            conf_ok = float(params.get('conf_okbtn', 0.85))
            # Giảm timeout xuống 0.3s để nhanh hơn
            found_ok = locate_template(otmpl, confidence=conf_ok, timeout=0.3, step=0.08, region=None)
            
            if found_ok is not None:
                x_ok, y_ok, val_ok = found_ok
                now = time.time()
                
                if now - last_click_ts < 1.2:
                    time.sleep(0.08)
                    return
                
                # QUAN TRỌNG: Kiểm tra loại popup trước khi xử lý
                self.log_fn(f"🔍 OkWatcher: Phát hiện nút OK - Kiểm tra loại popup...")
                popup_type = self._detect_popup_type(templates)
                self.log_fn(f"   → Kết quả: {popup_type or 'None (popup thường)'}")
                
                if popup_type == 'max_job':
                    # Popup "Đã làm tối đa job" → Chuyển tài khoản
                    self._handle_max_job_popup(x_ok, y_ok, templates, params)
                    return
                
                elif popup_type == 'blocked':
                    # Popup "Tài khoản bị block" → Lưu file + Chuyển tài khoản
                    self._handle_blocked_account_popup(x_ok, y_ok, templates, params)
                    return
                
                elif popup_type == 'fail':
                    # Popup fail job → Xử lý báo lỗi
                    self._handle_fail_before_ok(x_ok, y_ok, val_ok, templates, params, last_click_ts)
                    return
                
                else:
                    # Popup khác → Click OK bình thường
                    self.log_fn(f"OkWatcher: thấy OK (val={val_ok:.2f}) -> click tại ({int(x_ok)},{int(y_ok)})")
                    click_at(int(x_ok), int(y_ok))
                    last_click_ts = time.time()
                    time.sleep(0.6)
            else:
                time.sleep(0.08)
        except Exception as e:
            self.log_fn(f"OkWatcher lỗi khi match/nhấn OK: {e}")
            time.sleep(0.3)
    
    def _detect_popup_type(self, templates):
        """
        Phát hiện loại popup bằng OCR (gọi account_switcher)
        Returns: 'max_job', 'blocked', 'fail', None
        """
        try:
            # Ưu tiên dùng account_switcher để phát hiện (có OCR)
            if self.account_switcher:
                self.log_fn(f"   🔍 Dùng OCR để phát hiện loại popup...")
                popup_type = self.account_switcher.detect_error_popup_type()
                
                if popup_type:
                    return popup_type
            
            # Fallback: Kiểm tra fail icon (job fail)
            if self._check_fail_icon(templates, {}):
                self.log_fn(f"   ❌ Phát hiện fail icon (job thất bại)")
                return 'fail'
            
            # Không phát hiện được
            self.log_fn(f"   ❓ Không phát hiện được loại popup")
            return None
            
        except Exception as e:
            self.log_fn(f"OkWatcher: Lỗi khi phát hiện popup: {e}")
            import traceback
            self.log_fn(f"   {traceback.format_exc()}")
            return None
    
    def _handle_max_job_popup(self, x_ok, y_ok, templates, params):
        """Xử lý popup 'Đã làm tối đa job'"""
        try:
            self.log_fn("🔄 OkWatcher: Xử lý popup 'Đã làm tối đa job'...")
            
            # BƯỚC 1: Dừng sequence_worker trước (QUAN TRỌNG!)
            self.log_fn("   ⏸️ Tạm dừng thread tìm job...")
            sequence_worker_pause.set()
            time.sleep(0.5)  # Đợi sequence_worker dừng
            
            # BƯỚC 2: Suspend OkWatcher để không bị gián đoạn
            ok_watcher_suspend.set()
            
            # BƯỚC 3: Lưu tài khoản hiện tại vào danh sách max job (chỉ trong ngày)
            if self.account_switcher:
                self.account_switcher.handle_max_job_account()
            
            # BƯỚC 4: Click OK để đóng popup
            self.log_fn("   ✓ Click OK để đóng popup...")
            click_at(int(x_ok), int(y_ok))
            time.sleep(2.0)  # Đợi popup đóng hoàn toàn
            
            # BƯỚC 5: Gọi account_switcher để chuyển tài khoản
            if self.account_switcher:
                self.log_fn("   → Chuyển sang tài khoản khác...")
                success = self.account_switcher.switch_account(skip_ok_button=True)
                
                if success:
                    self.log_fn("   ✅ Đã chuyển tài khoản thành công!")
                    
                    # Reset navigation về trang "Kiếm thưởng"
                    self.log_fn("   🧭 Reset navigation về trang 'Kiếm thưởng'...")
                    try:
                        from Controllers.reset_navigation import ResetNavigation
                        
                        def should_stop():
                            return self._stop.is_set()
                        
                        resetter = ResetNavigation(templates, params, self.log_fn, should_stop)
                        resetter.perform_reset()
                        self.log_fn("   ✅ Reset navigation hoàn tất!")
                    except Exception as e:
                        self.log_fn(f"   ⚠️ Lỗi khi reset navigation: {e}")
                else:
                    self.log_fn("   ⚠️ Không thể chuyển tài khoản")
            else:
                self.log_fn("   ⚠️ Không có account_switcher")
            
            # BƯỚC 6: Resume cả OkWatcher và sequence_worker
            ok_watcher_suspend.clear()
            sequence_worker_pause.clear()
            self.log_fn("   ▶️ Tiếp tục thread tìm job...")
                
        except Exception as e:
            self.log_fn(f"OkWatcher: Lỗi khi xử lý max job popup: {e}")
            ok_watcher_suspend.clear()  # Đảm bảo resume
            sequence_worker_pause.clear()
    
    def _handle_blocked_account_popup(self, x_ok, y_ok, templates, params):
        """Xử lý popup 'Tài khoản bị block'"""
        try:
            self.log_fn("🔒 OkWatcher: Xử lý popup 'Tài khoản bị block'...")
            
            # Dừng sequence_worker trước
            self.log_fn("   ⏸️ Tạm dừng thread tìm job...")
            sequence_worker_pause.set()
            time.sleep(0.5)
            
            # Gọi account_switcher để xử lý
            if self.account_switcher:
                success = self.account_switcher.handle_blocked_account()
                
                if success:
                    self.log_fn("   ✅ Đã xử lý tài khoản bị block!")
                else:
                    self.log_fn("   ⚠️ Không thể xử lý blocked account")
            else:
                self.log_fn("   ⚠️ Không có account_switcher - Click OK")
                click_at(int(x_ok), int(y_ok))
                time.sleep(1.0)
            
            # Resume sequence_worker
            sequence_worker_pause.clear()
            self.log_fn("   ▶️ Tiếp tục thread tìm job...")
                
        except Exception as e:
            self.log_fn(f"OkWatcher: Lỗi khi xử lý blocked popup: {e}")
            sequence_worker_pause.clear()  # Đảm bảo resume

    def _check_fail_icon(self, templates, params):
        """Kiểm tra xem có fail icon không"""
        fail_path = templates.get('fail_icon')
        if fail_path and os.path.exists(fail_path):
            try:
                ftmpl = load_gray(fail_path)
                conf_fail = float(params.get('conf_fail', 0.9))
                f_found = locate_template(ftmpl, confidence=conf_fail, timeout=0.5, step=0.06, region=None)
                return f_found is not None
            except Exception as e:
                self.log_fn(f"OkWatcher: lỗi khi check fail_icon: {e}")
        return False

    def _handle_fail_before_ok(self, x_ok, y_ok, val_ok, templates, params, last_click_ts):
        """Xử lý khi phát hiện fail trước khi click OK"""
        self.log_fn(f"OkWatcher: Phát hiện FAIL trước khi OK (val_ok={val_ok:.2f}). Bắt đầu xử lý lỗi.")
        
        # Click OK để dismiss
        try:
            click_at(int(x_ok), int(y_ok))
            last_click_ts = time.time()
            time.sleep(0.5)
        except Exception as e:
            self.log_fn(f"OkWatcher: lỗi khi click OK để dismiss trước fail: {e}")
        
        # Tìm và click fail button
        fb_path = templates.get('fail_button')
        found_fb = False
        
        if fb_path and os.path.exists(fb_path):
            for i in range(4):
                if self._stop.is_set():
                    break
                try:
                    ftmpl2 = load_gray(fb_path)
                    fb_res = locate_template(
                        ftmpl2, 
                        confidence=float(params.get('conf_failbtn', 0.85)), 
                        timeout=0.8, step=0.06, region=None
                    )
                    if fb_res is not None:
                        self.log_fn("OkWatcher: Tìm thấy nút báo lỗi -> click")
                        click_at(fb_res[0], fb_res[1])
                        last_click_ts = time.time()
                        time.sleep(0.6)
                        found_fb = True
                        break
                except Exception as e:
                    self.log_fn(f"OkWatcher: lỗi khi tìm fail_button: {e}")
                
                # Cuộn để tìm nút (force=True khi xử lý fail)
                attempt_scroll_or_drag(force=True)
                time.sleep(0.45)
        
        if found_fb:
            self._handle_confirm_after_fail(templates, params, last_click_ts)
        else:
            self.log_fn("OkWatcher: Không tìm thấy nút báo lỗi sau cuộn/drag.")

    def _handle_confirm_after_fail(self, templates, params, last_click_ts):
        """Xử lý confirm sau khi báo lỗi"""
        # Cuộn để hiển thị confirm
        for _ in range(3):
            if self._stop.is_set():
                break
            attempt_scroll_or_drag(force=True)
            time.sleep(0.25)
        
        # Tìm confirm button
        confirm_path = templates.get('confirm_button')
        confirmed = False
        
        if confirm_path and os.path.exists(confirm_path):
            try:
                ctmpl = load_gray(confirm_path)
                cres = locate_template(
                    ctmpl, 
                    confidence=float(params.get('conf_okbtn', 0.85)), 
                    timeout=1.2, step=0.06, region=None
                )
                if cres is not None:
                    self.log_fn("OkWatcher: Tìm thấy Confirm -> click")
                    click_at(cres[0], cres[1])
                    last_click_ts = time.time()
                    time.sleep(0.6)
                    confirmed = True
            except Exception as e:
                self.log_fn(f"OkWatcher: lỗi khi tìm confirm_button: {e}")
        
        # Fallback: click OK
        if not confirmed:
            ok_path = templates.get('ok_button')
            if ok_path and os.path.exists(ok_path):
                try:
                    otmpl2 = load_gray(ok_path)
                    ok_res2 = locate_template(
                        otmpl2, 
                        confidence=float(params.get('conf_okbtn', 0.85)), 
                        timeout=1.2, step=0.06, region=None
                    )
                    if ok_res2 is not None:
                        self.log_fn("OkWatcher: Fallback click OK sau báo lỗi/confirm")
                        click_at(ok_res2[0], ok_res2[1])
                        last_click_ts = time.time()
                        time.sleep(0.6)
                except Exception as e:
                    self.log_fn(f"OkWatcher: lỗi fallback OK sau báo lỗi: {e}")
