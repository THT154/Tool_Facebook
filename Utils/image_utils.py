#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image_utils.py - Xử lý hình ảnh và template matching
"""
import os
import time
import shutil
import cv2
import numpy as np
import pyautogui
from Models.config import TEMPLATES_DIR

# ADB mode
_use_adb_mode = False
_adb_controller = None

def set_adb_mode(enabled, adb_controller=None):
    """Bật/tắt chế độ ADB cho image utils"""
    global _use_adb_mode, _adb_controller
    _use_adb_mode = enabled
    if enabled and adb_controller:
        _adb_controller = adb_controller

def load_gray(path):
    """Load ảnh dưới dạng grayscale"""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)
    return img

def screenshot_gray(region=None):
    """
    Chụp màn hình và chuyển sang grayscale
    - Nếu ADB mode: chụp từ LDPlayer qua ADB (region bị bỏ qua)
    - Nếu không: dùng pyautogui
    """
    if _use_adb_mode and _adb_controller:
        # ADB mode: chụp từ LDPlayer
        gray = _adb_controller.screenshot_gray()
        if gray is not None:
            return gray
        # Fallback to pyautogui nếu ADB fail
    
    # Pyautogui mode
    if region:
        ss = pyautogui.screenshot(region=region)
    else:
        ss = pyautogui.screenshot()
    arr = np.array(ss)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return gray

def robust_match_template(screen_img, tmpl_img):
    """Match template với xử lý resize nếu template lớn hơn màn hình"""
    sh, sw = screen_img.shape[:2]
    th, tw = tmpl_img.shape[:2]
    
    if th > sh or tw > sw:
        scale_y = sh / th
        scale_x = sw / tw
        scale = min(scale_x, scale_y, 1.0)
        new_w = max(1, int(tw * scale))
        new_h = max(1, int(th * scale))
        tmpl_resized = cv2.resize(tmpl_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(screen_img, tmpl_resized, cv2.TM_CCOEFF_NORMED)
        return res, (new_w, new_h)
    else:
        res = cv2.matchTemplate(screen_img, tmpl_img, cv2.TM_CCOEFF_NORMED)
        return res, (tw, th)

def locate_template(template_img, confidence=0.85, timeout=0.3, step=0.08, region=None):
    """
    Tìm template trên màn hình với timeout
    Returns: (x, y, confidence) hoặc None
    
    Tối ưu: step=0.08 (thay vì 0.05) để giảm số lần check
    """
    t0 = time.time()
    while True:
        try:
            if region:
                screen = screenshot_gray(region=region)
                base_x, base_y = region[0], region[1]
            else:
                screen = screenshot_gray(region=None)
                base_x, base_y = 0, 0
        except Exception:
            return None
        
        try:
            res, used_size = robust_match_template(screen, template_img)
        except Exception:
            return None
        
        minv, maxv, minloc, maxloc = cv2.minMaxLoc(res)
        if maxv >= confidence:
            used_tw, used_th = used_size
            x = maxloc[0] + used_tw//2 + base_x
            y = maxloc[1] + used_th//2 + base_y
            return (x, y, float(maxv))
        
        if time.time() - t0 > timeout:
            return None
        time.sleep(step)

def locate_template_multiscale(template_img, confidence=0.85, timeout=1.5, step=0.05, 
                                region=None, scales=(1.0, 0.95, 1.05, 0.9, 1.1)):
    """
    Tìm template với nhiều scale khác nhau
    Returns: (x, y, confidence) hoặc None
    """
    t_start = time.time()
    per_scale_timeout = max(0.2, timeout / max(1, len(scales)))
    
    for s in scales:
        elapsed = time.time() - t_start
        if elapsed >= timeout:
            break
        
        try:
            if s == 1.0:
                tmpl_try = template_img
            else:
                new_w = max(1, int(template_img.shape[1] * s))
                new_h = max(1, int(template_img.shape[0] * s))
                tmpl_try = cv2.resize(template_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        except Exception:
            tmpl_try = template_img
        
        found = locate_template(tmpl_try, confidence=confidence, 
                               timeout=min(per_scale_timeout, timeout - elapsed), 
                               step=step, region=region)
        if found is not None:
            return found
    
    return None

def copy_template_to_store(src_path, key):
    """Copy template vào thư mục templates"""
    if not os.path.exists(src_path):
        raise FileNotFoundError(src_path)
    ext = os.path.splitext(src_path)[1].lower() or ".png"
    dst = os.path.join(TEMPLATES_DIR, f"{key}{ext}")
    shutil.copy2(src_path, dst)
    return dst

def clear_screenshot_cache():
    """Xóa cache screenshot để giải phóng memory"""
    try:
        # Clear any global caches
        import gc
        gc.collect()
        
        # Reset screenshot buffers nếu có
        global _screenshot_buffer
        if '_screenshot_buffer' in globals():
            _screenshot_buffer = None
        
        return True
    except Exception:
        return False