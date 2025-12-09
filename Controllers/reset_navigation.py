#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reset_navigation.py - Xử lý reset điều hướng khi không tìm thấy job
"""
import os
import time
import pyautogui
from Controllers.ok_watcher import ok_watcher_suspend
from Utils.image_utils import load_gray, locate_template, locate_template_multiscale
from Utils.window_utils import click_at, get_ldplayer_window

try:
    import pygetwindow as gw
except Exception:
    gw = None

class ResetNavigation:
    """Class xử lý reset điều hướng về Golike"""
    
    def __init__(self, templates, params, log_fn, should_stop_fn):
        self.templates = templates
        self.params = params
        self.log_fn = log_fn
        self.should_stop_fn = should_stop_fn
    
    def perform_reset(self):
        """Thực hiện reset điều hướng"""
        self.log_fn("⚠ Không thấy job quá ngưỡng; thực hiện reset điều hướng (Danh mục -> Kiếm tiền)...")
        ok_watcher_suspend.set()
        
        try:
            # 1) Click category button (Danh mục)
            clicked_cat = self._try_click_template_keys(
                ['category_button', 'btn_category', 'danh_muc'], 
                'conf_job', timeout_per_try=1.2, retries=4
            )
            
            if not clicked_cat:
                self._handle_no_category_button()
            
            time.sleep(0.5)
            
            # 2) Click earn money button (Kiếm tiền) - PHẢI TÌM ĐƯỢC MỚI TIẾP TỤC
            clicked_earn = self._try_click_template_keys(
                ['earn_button', 'kiem_tien', 'btn_earn', 'earn_money'], 
                'conf_job', timeout_per_try=1.2, retries=8  # Tăng retry
            )
            
            if not clicked_earn:
                self.log_fn("Reset: ❌ KHÔNG TÌM THẤY MỤC KIẾM TIỀN!")
                self.log_fn("Reset: 🔄 Thử lại từ đầu...")
                # Thử lại toàn bộ quá trình
                self._retry_full_reset()
                return
            
            time.sleep(1.0)
            self.log_fn("Reset: ✅ Đã vào mục Kiếm tiền - Điều hướng hoàn tất!")
        finally:
            ok_watcher_suspend.clear()
    
    def _try_click_template_keys(self, keys, conf_key, timeout_per_try=1.0, retries=4):
        """Thử click một trong các template keys"""
        for key in keys:
            path = self.templates.get(key)
            if not path or not os.path.exists(path):
                continue
            
            for i in range(retries):
                if self.should_stop_fn():
                    return False
                
                try:
                    from Utils.window_utils import is_adb_mode
                    
                    tmpl = load_gray(path)
                    conf = float(self.params.get(conf_key, 0.85))
                    region = None
                    
                    # Chỉ dùng region khi không phải ADB mode
                    if not is_adb_mode():
                        ld2 = get_ldplayer_window()
                        if ld2:
                            left2, top2, w2, h2, _ = ld2
                            region = (left2, top2, w2, h2)
                    
                    found = locate_template(
                        tmpl, confidence=conf, 
                        timeout=timeout_per_try, 
                        step=0.06, region=region
                    )
                    
                    if found is not None:
                        x, y, _ = found
                        self.log_fn(f"Reset: Tìm thấy '{key}' -> click")
                        click_at(x, y)
                        time.sleep(0.6)
                        return True
                except Exception as e:
                    self.log_fn(f"Reset: lỗi khi tìm '{key}': {e}")
                
                time.sleep(0.04)
        
        return False
    
    def _handle_no_category_button(self):
        """Xử lý khi không tìm thấy nút Danh mục - Dùng ADB mở Golike"""
        self.log_fn("Reset: Không tìm thấy nút Danh mục. Dùng ADB mở Golike...")
        
        try:
            from Utils.window_utils import is_adb_mode
            from Utils.adb_utils import get_adb_controller
            
            if is_adb_mode():
                controller = get_adb_controller()
                if controller:
                    # Nhấn Home để về màn hình chính
                    self.log_fn("Reset: 🏠 Nhấn Home...")
                    controller.press_home()
                    time.sleep(2)
                    
                    # Mở Golike bằng package name
                    golike_package = self.params.get('golike_package', 'com.golike.app')
                    self.log_fn(f"Reset: 📱 Mở Golike ({golike_package})...")
                    success = controller.open_app(golike_package)
                    
                    if success:
                        self.log_fn("Reset: ✓ Đã mở Golike bằng ADB")
                        time.sleep(3)
                        return
                    else:
                        self.log_fn("Reset: ❌ Không mở được Golike bằng ADB")
                else:
                    self.log_fn("Reset: ❌ Không có ADB controller")
            else:
                self.log_fn("Reset: ❌ Không ở ADB mode")
            
            # Fallback: Cách cũ (tìm icon)
            self.log_fn("Reset: 🔄 Fallback - Tìm icon Golike...")
            self._fallback_find_golike()
            
        except Exception as e:
            self.log_fn(f"Reset: ❌ Lỗi khi mở Golike: {e}")
            self._fallback_find_golike()
    
    def _fallback_find_golike(self):
        """Fallback: Tìm icon Golike (cách cũ)"""
        try:
            pyautogui.press('esc')
            ld_for_focus = get_ldplayer_window()
            
            if ld_for_focus:
                l_left, l_top, l_w, l_h, l_win = ld_for_focus
                
                # Activate window
                try:
                    l_win.activate()
                except Exception:
                    try:
                        l_win.restore()
                        l_win.activate()
                    except Exception:
                        pass
                
                # Click center
                try:
                    click_at(l_left + l_w//2, l_top + l_h//2)
                except Exception:
                    pass
            
            time.sleep(0.7)
            
            # Tìm và click Golike icon
            self._find_and_click_golike(ld_for_focus)
        except Exception as e:
            self.log_fn(f"Reset: ❌ Lỗi fallback: {e}")
    
    def _find_and_click_golike(self, ld_window):
        """Tìm và click Golike icon"""
        golike_keys = ('golike_icon', 'ld_golike_icon', 'golike')
        found_golike = False
        
        for gk in golike_keys:
            gpath = self.templates.get(gk)
            if not gpath or not os.path.exists(gpath):
                continue
            
            try:
                gtmpl = load_gray(gpath)
                conf_g = float(self.params.get('conf_golike', self.params.get('conf_job', 0.85)))
                
                # Tìm trong LDPlayer region
                region = None
                if ld_window:
                    region = (ld_window[0], ld_window[1], ld_window[2], ld_window[3])
                
                self.log_fn(f"Reset: tìm Golike '{gk}' trong region={region} với conf={conf_g}")
                gres = locate_template_multiscale(
                    gtmpl, confidence=conf_g, timeout=1.8, 
                    step=0.06, region=region, 
                    scales=(1.0, 0.95, 1.05, 0.9, 1.1)
                )
                
                if gres is not None:
                    self.log_fn(f"Reset: Tìm thấy Golike icon '{gk}' (score={gres[2]:.2f}) -> click")
                    click_at(gres[0], gres[1])
                    time.sleep(0.8)
                    found_golike = True
                    break
            except Exception as e:
                self.log_fn(f"Reset: lỗi khi tìm/ấn golike '{gk}': {e}")
        
        if not found_golike:
            # Fallback: tìm toàn màn hình
            self._find_golike_fallback(golike_keys)
    
    def _find_golike_fallback(self, golike_keys):
        """Fallback: tìm Golike toàn màn hình"""
        conf_fb = float(self.params.get('conf_golike_fallback', 0.80))
        
        for gk in golike_keys:
            gpath = self.templates.get(gk)
            if not gpath or not os.path.exists(gpath):
                continue
            
            try:
                gtmpl = load_gray(gpath)
                self.log_fn(f"Reset: fallback tìm Golike toàn màn hình '{gk}' với conf={conf_fb}")
                gres = locate_template_multiscale(
                    gtmpl, confidence=conf_fb, timeout=1.6, 
                    step=0.06, region=None, 
                    scales=(1.0, 0.95, 1.05)
                )
                
                if gres is not None:
                    self.log_fn(f"Reset: Tìm thấy Golike icon '{gk}' (fallback) -> click")
                    click_at(gres[0], gres[1])
                    time.sleep(0.8)
                    return
            except Exception:
                pass
        
        self.log_fn("Reset: Không tìm thấy Golike icon sau focus/click trung tâm.")
    
    def _retry_full_reset(self):
        """Thử lại toàn bộ quá trình reset (dùng ADB mở Golike)"""
        try:
            self.log_fn("Reset: 📱 Dùng ADB mở lại Golike...")
            
            # Dùng ADB mở Golike
            from Utils.window_utils import is_adb_mode
            from Utils.adb_utils import get_adb_controller
            
            if is_adb_mode():
                controller = get_adb_controller()
                if controller:
                    # Nhấn Home trước
                    controller.press_home()
                    time.sleep(2)
                    
                    # Mở Golike bằng package name
                    golike_package = self.params.get('golike_package', 'com.golike.app')
                    success = controller.open_app(golike_package)
                    
                    if success:
                        self.log_fn("Reset: ✓ Đã mở Golike bằng ADB")
                        time.sleep(3)
                        
                        # Thử tìm "Kiếm tiền" lại
                        clicked_earn = self._try_click_template_keys(
                            ['earn_button', 'kiem_tien', 'btn_earn', 'earn_money'], 
                            'conf_job', timeout_per_try=2.0, retries=5
                        )
                        
                        if clicked_earn:
                            self.log_fn("Reset: ✅ Đã tìm thấy và click 'Kiếm tiền'!")
                        else:
                            self.log_fn("Reset: ❌ Vẫn không tìm thấy 'Kiếm tiền' sau khi mở Golike")
                    else:
                        self.log_fn("Reset: ❌ Không mở được Golike bằng ADB")
                else:
                    self.log_fn("Reset: ❌ Không có ADB controller")
            else:
                self.log_fn("Reset: ❌ Không ở ADB mode - Không thể mở Golike")
                
        except Exception as e:
            self.log_fn(f"Reset: ❌ Lỗi khi retry full reset: {e}")
    
    def _log_windows(self):
        """Log danh sách windows để debug"""
        if gw is None:
            self.log_fn("Reset: pygetwindow không có (gw=None)")
            return
        
        try:
            win_titles = [
                (w.title, getattr(w, 'left', None), getattr(w, 'top', None)) 
                for w in gw.getAllWindows()
            ]
            self.log_fn(f"Reset: Window titles sample: {win_titles[:12]}")
        except Exception as e:
            self.log_fn(f"Reset: lỗi khi liệt kê window titles: {e}")
