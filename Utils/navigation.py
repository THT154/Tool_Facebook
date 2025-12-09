#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
navigation.py - Xử lý điều hướng và back actions
"""
import time
import pyautogui
from Utils.window_utils import click_at, get_ldplayer_window
from Utils.image_utils import load_gray, locate_template_multiscale

def press_back_method(method, back_coord=None, templates=None, params=None):
    """
    Thực hiện hành động BACK theo method được chọn
    - click: click vào tọa độ
    - key: nhấn phím F2 hoặc Alt+Left
    - focus_golike: focus vào LDPlayer và tìm icon Golike
    """
    if method == 'click' and back_coord:
        x, y = back_coord
        click_at(x, y)
        return True
    
    elif method == 'key':
        from Utils.window_utils import is_adb_mode, get_adb_controller
        
        if is_adb_mode():
            # ADB mode: Dùng Back button của Android (chuẩn nhất)
            controller = get_adb_controller()
            if controller:
                try:
                    # Dùng Back button - cách chuẩn trong Android
                    controller.press_back()
                    time.sleep(0.1)
                    controller.press_back()
                    return True
                except Exception as e:
                    print(f"Lỗi ADB press_back: {e}")
                    return False
            return False
        else:
            # Pyautogui mode: Dùng F2 hoặc Alt+Left
            try:
                pyautogui.press('f2')
                pyautogui.press('f2')
                return True
            except Exception:
                try:
                    pyautogui.keyDown('alt')
                    pyautogui.press('left')
                    pyautogui.keyUp('alt')
                    return True
                except Exception:
                    return False
    
    elif method == 'focus_golike':
        return _focus_golike_method(back_coord, templates, params)
    
    return False

def _focus_golike_method(back_coord, templates, params):
    """Xử lý focus vào Golike app trong LDPlayer"""
    try:
        from Utils.window_utils import is_adb_mode
        
        # Kiểm tra ADB mode
        if is_adb_mode():
            # ADB mode: Mở app Golike trực tiếp bằng package name
            from Utils.window_utils import get_adb_controller
            
            controller = get_adb_controller()
            if controller:
                try:
                    # Mở app Golike trực tiếp (không cần tìm icon)
                    print("[FOCUS_GOLIKE] ADB mode: Mở app Golike...")
                    
                    # Package name của Golike (có thể cần điều chỉnh)
                    golike_package = params.get('golike_package', 'com.golike.app') if params else 'com.golike.app'
                    
                    success = controller.open_app(golike_package)
                    if success:
                        print(f"[FOCUS_GOLIKE] Đã mở app Golike: {golike_package}")
                        time.sleep(1.0)  # Đợi app load
                        return True
                    else:
                        print(f"[FOCUS_GOLIKE] Không thể mở app Golike: {golike_package}")
                        print("[FOCUS_GOLIKE] Gợi ý: Kiểm tra package name trong GUI")
                        return False
                except Exception as e:
                    print(f"[FOCUS_GOLIKE] Lỗi open_app: {e}")
                    return False
            
            return False
        
        # Pyautogui mode: Cần activate window và dùng region
        ld = get_ldplayer_window()
        if ld:
            left, top, w, h, win_obj = ld
            
            # Activate window
            try:
                win_obj.activate()
            except Exception:
                try:
                    win_obj.restore()
                    win_obj.activate()
                except Exception:
                    pass
            
            time.sleep(0.12)
            
            # Press F1 helper
            try:
                pyautogui.press('f1')
            except Exception:
                try:
                    cx = left + w // 2
                    cy = top + h // 2
                    click_at(cx, cy)
                except Exception:
                    pass
            
            time.sleep(0.25)
            
            # Tìm và click Golike icon
            if templates:
                for keyname in ('golike_icon', 'ld_golike_icon', 'golike'):
                    path = templates.get(keyname)
                    if path:
                        try:
                            tmpl = load_gray(path)
                            conf = float(params.get('conf_golike', params.get('conf_job', 0.85))) if params else 0.85
                            found = locate_template_multiscale(
                                tmpl, confidence=conf, timeout=1.2, 
                                step=0.06, region=(left, top, w, h)
                            )
                            if found is not None:
                                x, y, _ = found
                                click_at(x, y)
                                click_at(x, y)
                                time.sleep(0.6)
                                return True
                        except Exception:
                            pass
            
            # Fallback: click center
            try:
                cx = left + w // 2
                cy = top + h // 2
                click_at(cx, cy)
                time.sleep(0.2)
            except Exception:
                pass
            
            # Try global find
            if templates:
                for keyname in ('golike_icon', 'ld_golike_icon', 'golike'):
                    path = templates.get(keyname)
                    if path:
                        try:
                            tmpl = load_gray(path)
                            conf = float(params.get('conf_golike_fallback', 0.80)) if params else 0.80
                            found2 = locate_template_multiscale(
                                tmpl, confidence=conf, timeout=1.5, 
                                step=0.06, region=None
                            )
                            if found2 is not None:
                                x, y, _ = found2
                                click_at(x, y)
                                time.sleep(0.6)
                                return True
                        except Exception:
                            pass
            return True
        else:
            # Fallback nếu không tìm thấy LDPlayer
            if back_coord:
                try:
                    click_at(back_coord[0], back_coord[1])
                    return True
                except Exception:
                    pass
            try:
                pyautogui.press('esc')
                return True
            except Exception:
                return False
    except Exception:
        try:
            pyautogui.press('esc')
            return True
        except Exception:
            return False
