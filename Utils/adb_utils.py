#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adb_utils.py - Xử lý ADB cho LDPlayer (click ảo, screenshot)
"""
import subprocess
import time
import cv2
import numpy as np
from PIL import Image
import io

class ADBController:
    """Controller để điều khiển LDPlayer qua ADB"""
    
    def __init__(self, adb_path="adb", device_id=None):
        """
        Args:
            adb_path: Đường dẫn đến adb.exe (mặc định tìm trong PATH)
            device_id: ID của device (None = auto detect)
        """
        self.adb_path = adb_path
        self.device_id = device_id
        self.connected = False
        
    def connect(self, port=5555, device_id=None):
        """
        Kết nối đến LDPlayer qua ADB
        
        Args:
            port: Port để kết nối (mặc định 5555)
            device_id: Device ID cụ thể (nếu có nhiều devices)
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            # Nếu có device_id cụ thể, dùng luôn
            if device_id:
                self.device_id = device_id
                self.connected = True
                return True
            
            # Thử kết nối localhost
            cmd = [self.adb_path, "connect", f"127.0.0.1:{port}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if "connected" in result.stdout.lower() or "already connected" in result.stdout.lower():
                # Kiểm tra số lượng devices
                devices = self.get_devices()
                
                if len(devices) == 0:
                    print("Không tìm thấy device nào")
                    return False
                elif len(devices) == 1:
                    # Chỉ có 1 device, dùng luôn
                    self.device_id = devices[0]
                    self.connected = True
                    return True
                else:
                    # Có nhiều devices, cần chọn
                    # Thử tìm device với port vừa connect
                    target_device = f"127.0.0.1:{port}"
                    if target_device in devices:
                        self.device_id = target_device
                        self.connected = True
                        return True
                    else:
                        # Không tìm thấy, báo lỗi
                        print(f"Có {len(devices)} devices. Cần chỉ định device_id cụ thể.")
                        return False
            return False
        except Exception as e:
            print(f"Lỗi kết nối ADB: {e}")
            return False
    
    def get_devices(self):
        """Lấy danh sách devices đang kết nối"""
        try:
            cmd = [self.adb_path, "devices"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')[1:]  # Bỏ dòng header
            devices = []
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[1] == 'device':
                        devices.append(parts[0])
            return devices
        except Exception:
            return []
    
    def _run_adb_command(self, *args, timeout=10):
        """Chạy lệnh ADB"""
        if self.device_id:
            cmd = [self.adb_path, "-s", self.device_id] + list(args)
        else:
            cmd = [self.adb_path] + list(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout)
            return result
        except Exception as e:
            print(f"Lỗi chạy ADB command: {e}")
            return None
    
    def tap(self, x, y):
        """Click tại vị trí (x, y) trong LDPlayer"""
        if not self.connected:
            print(f"ADB tap failed: Not connected")
            return False
        
        try:
            # Debug: In ra command
            cmd_str = f"adb -s {self.device_id} shell input tap {int(x)} {int(y)}"
            print(f"[DEBUG] ADB tap command: {cmd_str}")
            
            result = self._run_adb_command("shell", "input", "tap", str(int(x)), str(int(y)))
            
            if result is None:
                print(f"ADB tap failed: Command returned None")
                return False
            
            if result.returncode != 0:
                print(f"ADB tap failed: Return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
                return False
            
            print(f"[DEBUG] ADB tap success at ({int(x)}, {int(y)})")
            return True
        except Exception as e:
            print(f"Lỗi tap: {e}")
            return False
    
    def swipe(self, x1, y1, x2, y2, duration=300):
        """Vuốt từ (x1,y1) đến (x2,y2)"""
        if not self.connected:
            return False
        
        try:
            result = self._run_adb_command(
                "shell", "input", "swipe", 
                str(int(x1)), str(int(y1)), 
                str(int(x2)), str(int(y2)), 
                str(int(duration))
            )
            return result is not None and result.returncode == 0
        except Exception as e:
            print(f"Lỗi swipe: {e}")
            return False
    
    def screenshot(self):
        """
        Chụp screenshot từ LDPlayer
        Returns: numpy array (BGR format) hoặc None
        """
        if not self.connected:
            return None
        
        try:
            # Chụp screenshot và lưu vào device
            result = self._run_adb_command("shell", "screencap", "-p", timeout=5)
            
            if result and result.returncode == 0:
                # Convert bytes to image
                img_bytes = result.stdout
                # Fix line endings (Windows issue)
                img_bytes = img_bytes.replace(b'\r\n', b'\n')
                
                # Load image
                img = Image.open(io.BytesIO(img_bytes))
                # Convert to numpy array (RGB)
                img_array = np.array(img)
                # Convert RGB to BGR for OpenCV
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                return img_bgr
            return None
        except Exception as e:
            print(f"Lỗi screenshot: {e}")
            return None
    
    def screenshot_gray(self):
        """Chụp screenshot và convert sang grayscale"""
        img = self.screenshot()
        if img is not None:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return None
    
    def get_screen_size(self):
        """Lấy kích thước màn hình LDPlayer"""
        if not self.connected:
            return None
        
        try:
            result = self._run_adb_command("shell", "wm", "size")
            if result and result.returncode == 0:
                # Output: Physical size: 1080x1920
                output = result.stdout.decode('utf-8')
                if 'Physical size:' in output:
                    size_str = output.split('Physical size:')[1].strip()
                    w, h = map(int, size_str.split('x'))
                    return (w, h)
            return None
        except Exception:
            return None
    
    def press_key(self, keycode):
        """
        Nhấn phím bằng keycode
        
        Common keycodes:
        - KEYCODE_BACK (4): Nút Back
        - KEYCODE_HOME (3): Nút Home
        - KEYCODE_ESCAPE (111): ESC
        - KEYCODE_F1 (131): F1
        - KEYCODE_F2 (132): F2
        """
        if not self.connected:
            print(f"ADB press_key failed: Not connected")
            return False
        
        try:
            print(f"[DEBUG] ADB press key: {keycode}")
            result = self._run_adb_command("shell", "input", "keyevent", str(keycode))
            
            if result is None:
                print(f"ADB press_key failed: Command returned None")
                return False
            
            if result.returncode != 0:
                print(f"ADB press_key failed: Return code {result.returncode}")
                return False
            
            print(f"[DEBUG] ADB press_key success: {keycode}")
            return True
        except Exception as e:
            print(f"Lỗi press_key: {e}")
            return False
    
    def press_back(self):
        """Nhấn nút Back"""
        return self.press_key("KEYCODE_BACK")
    
    def press_home(self):
        """Nhấn nút Home"""
        return self.press_key("KEYCODE_HOME")
    
    def press_escape(self):
        """Nhấn phím ESC"""
        return self.press_key("KEYCODE_ESCAPE")
    
    def press_f2(self):
        """Nhấn phím F2"""
        return self.press_key("KEYCODE_F2")
    
    def open_app(self, package_name):
        """
        Mở app bằng package name
        
        Args:
            package_name: Package name của app (vd: "com.golike.app")
        
        Returns:
            True nếu thành công
        """
        if not self.connected:
            print(f"ADB open_app failed: Not connected")
            return False
        
        try:
            print(f"[DEBUG] ADB open app: {package_name}")
            # Dùng monkey để mở app
            result = self._run_adb_command(
                "shell", "monkey", "-p", package_name, "-c", 
                "android.intent.category.LAUNCHER", "1"
            )
            
            if result is None:
                print(f"ADB open_app failed: Command returned None")
                return False
            
            if result.returncode != 0:
                print(f"ADB open_app failed: Return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr.decode('utf-8', errors='ignore')}")
                return False
            
            print(f"[DEBUG] ADB open_app success: {package_name}")
            return True
        except Exception as e:
            print(f"Lỗi open_app: {e}")
            return False
    
    def get_current_package(self):
        """
        Lấy package name của app đang chạy
        
        Returns:
            Package name hoặc None
        """
        if not self.connected:
            return None
        
        try:
            result = self._run_adb_command(
                "shell", "dumpsys", "window", "windows", "|", "grep", "-E", "mCurrentFocus"
            )
            
            if result and result.returncode == 0:
                output = result.stdout.decode('utf-8', errors='ignore')
                # Parse output: mCurrentFocus=Window{... u0 com.package.name/...}
                if 'mCurrentFocus' in output:
                    parts = output.split()
                    for part in parts:
                        if '/' in part:
                            package = part.split('/')[0]
                            return package
            return None
        except Exception:
            return None

# Global instance
_adb_controller = None

def get_adb_controller():
    """Lấy ADB controller instance (singleton)"""
    global _adb_controller
    if _adb_controller is None:
        _adb_controller = ADBController()
    return _adb_controller

def init_adb_connection(adb_path="adb", port=5555):
    """Khởi tạo kết nối ADB"""
    controller = get_adb_controller()
    controller.adb_path = adb_path
    return controller.connect(port)
