#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
window_utils.py - Xử lý window và click actions
"""
import time
import random
import pyautogui

try:
    import pygetwindow as gw
except Exception:
    gw = None

# ADB mode flag
_use_adb_mode = False
_adb_controller = None

def set_adb_mode(enabled, adb_controller=None):
    """Bật/tắt chế độ ADB"""
    global _use_adb_mode, _adb_controller
    _use_adb_mode = enabled
    if enabled and adb_controller:
        _adb_controller = adb_controller

def is_adb_mode():
    """Kiểm tra có đang dùng ADB mode không"""
    return _use_adb_mode

def get_adb_controller():
    """Lấy ADB controller"""
    return _adb_controller

def click_at(x, y):
    """
    Click tại vị trí
    - Nếu ADB mode: click trong LDPlayer bằng ADB (không chiếm chuột)
    - Nếu không: dùng pyautogui (click chuột thật)
    """
    if _use_adb_mode and _adb_controller:
        # ADB mode: click ảo trong LDPlayer
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        final_x = x + offset_x
        final_y = y + offset_y
        
        print(f"[CLICK_AT] ADB mode: Clicking at ({final_x}, {final_y}) [original: ({x}, {y})]")
        
        result = _adb_controller.tap(final_x, final_y)
        time.sleep(0.04)  # Thêm delay nhỏ
        return result
    else:
        # Pyautogui mode: click chuột thật
        print(f"[CLICK_AT] Pyautogui mode: Clicking at ({x}, {y})")
        pyautogui.moveTo(
            x + random.randint(-3, 3), 
            y + random.randint(-3, 3), 
            duration=random.uniform(0.06, 0.18)
        )
        pyautogui.click()
        time.sleep(0.04)
        return True

def get_ldplayer_window():
    """Tìm và trả về thông tin window LDPlayer"""
    if gw is None:
        return None
    
    try:
        wins = gw.getAllWindows()
    except Exception:
        return None
    
    for w in wins:
        title = (w.title or "").lower()
        if 'ldplayer' in title or 'ld player' in title or 'ld' in title:
            try:
                return (w.left, w.top, w.width, w.height, w)
            except Exception:
                try:
                    return (w.topleft.x, w.topleft.y, w.width, w.height, w)
                except Exception:
                    return None
    return None

def attempt_scroll_or_drag(force=False):
    """
    Cuộn hoặc drag màn hình
    CHỈ thực hiện khi force=True
    """
    if not force:
        return False
    
    if _use_adb_mode and _adb_controller:
        # ADB mode: swipe trong LDPlayer
        try:
            screen_size = _adb_controller.get_screen_size()
            if screen_size:
                w, h = screen_size
                cx, cy = w // 2, h // 2
                # Swipe từ giữa màn hình lên trên
                _adb_controller.swipe(cx, cy + 200, cx, cy - 200, duration=300)
                time.sleep(0.25)
                return True
            return False
        except Exception:
            return False
    else:
        # Pyautogui mode
        try:
            pyautogui.scroll(-600)
            time.sleep(0.25)
            return True
        except Exception:
            try:
                w, h = pyautogui.size()
                cx, cy = w // 2, h // 2
                pyautogui.moveTo(cx, cy, duration=0.12)
                pyautogui.dragRel(0, -400, duration=0.35)
                time.sleep(0.25)
                return True
            except Exception:
                return False
