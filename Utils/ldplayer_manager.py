#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ldplayer_manager.py - Quản lý LDPlayer (restart, clear cache)
"""
import subprocess
import time
import psutil

class LDPlayerManager:
    """Manager để quản lý LDPlayer"""
    
    def __init__(self, ldplayer_path=None):
        """
        Args:
            ldplayer_path: Đường dẫn đến LDPlayer (vd: C:\\LDPlayer\\LDPlayer4.0)
        """
        self.ldplayer_path = ldplayer_path or self._find_ldplayer_path()
    
    def _find_ldplayer_path(self):
        """Tự động tìm đường dẫn LDPlayer"""
        common_paths = [
            "C:\\LDPlayer\\LDPlayer4.0",
            "C:\\LDPlayer\\LDPlayer9",
            "D:\\LDPlayer\\LDPlayer4.0",
            "D:\\LDPlayer\\LDPlayer9",
        ]
        
        for path in common_paths:
            import os
            if os.path.exists(path):
                return path
        
        return None
    
    def is_ldplayer_running(self):
        """Kiểm tra LDPlayer có đang chạy không"""
        for proc in psutil.process_iter(['name']):
            try:
                if 'ldplayer' in proc.info['name'].lower() or 'dnplayer' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    def kill_ldplayer(self):
        """Tắt LDPlayer"""
        print("🔴 Đang tắt LDPlayer...")
        killed = False
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = proc.info['name'].lower()
                if 'ldplayer' in name or 'dnplayer' in name:
                    proc.kill()
                    killed = True
                    print(f"   ✓ Đã tắt process: {proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed:
            time.sleep(3)  # Đợi process tắt hoàn toàn
            print("✓ LDPlayer đã tắt")
        else:
            print("⚠️ Không tìm thấy LDPlayer đang chạy")
        
        return killed
    
    def start_ldplayer(self, index=0):
        """
        Khởi động LDPlayer
        
        Args:
            index: Index của emulator (0, 1, 2...)
        """
        if not self.ldplayer_path:
            print("❌ Không tìm thấy đường dẫn LDPlayer")
            return False
        
        print(f"🟢 Đang khởi động LDPlayer (index {index})...")
        
        try:
            import os
            ldconsole = os.path.join(self.ldplayer_path, "ldconsole.exe")
            
            if not os.path.exists(ldconsole):
                print(f"❌ Không tìm thấy ldconsole.exe tại: {ldconsole}")
                return False
            
            # Khởi động emulator
            subprocess.Popen([ldconsole, "launch", f"--index", str(index)])
            
            print(f"✓ Đã gửi lệnh khởi động")
            print(f"⏳ Đợi LDPlayer khởi động (30 giây)...")
            time.sleep(10)  # Đợi LDPlayer khởi động
            
            if self.is_ldplayer_running():
                print("✓ LDPlayer đã khởi động thành công")
                return True
            else:
                print("⚠️ LDPlayer chưa khởi động xong, vui lòng đợi thêm")
                return False
            
        except Exception as e:
            print(f"❌ Lỗi khi khởi động LDPlayer: {e}")
            return False
    
    def restart_ldplayer(self, index=0):
        """
        Restart LDPlayer
        
        Args:
            index: Index của emulator
        """
        print("🔄 Đang restart LDPlayer...")
        
        # Tắt
        self.kill_ldplayer()
        
        # Đợi
        time.sleep(5)
        
        # Khởi động lại
        return self.start_ldplayer(index)
    
    def clear_cache(self, index=0):
        """
        Xóa cache của LDPlayer
        
        Args:
            index: Index của emulator
        """
        if not self.ldplayer_path:
            print("❌ Không tìm thấy đường dẫn LDPlayer")
            return False
        
        print(f"🧹 Đang xóa cache LDPlayer (index {index})...")
        
        try:
            import os
            ldconsole = os.path.join(self.ldplayer_path, "ldconsole.exe")
            
            # Xóa cache
            subprocess.run([ldconsole, "action", f"--index", str(index), "--key", "call.cleaner"])
            
            print("✓ Đã xóa cache")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi xóa cache: {e}")
            return False

# Test
if __name__ == "__main__":
    manager = LDPlayerManager()
    
    print("=== LDPlayer Manager ===\n")
    print(f"LDPlayer path: {manager.ldplayer_path}")
    print(f"Is running: {manager.is_ldplayer_running()}")
    
    # Uncomment để test
    # manager.restart_ldplayer(index=0)
