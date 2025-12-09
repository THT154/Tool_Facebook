#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Entry point của ứng dụng Golike Sequence Bot
"""
import signal
import tkinter as tk
import pyautogui

from Models.config import ensure_directories
from gui import App

# Cấu hình pyautogui
pyautogui.FAILSAFE = True

def main():
    """Hàm main khởi động ứng dụng"""
    # Tạo thư mục cần thiết
    ensure_directories()
    
    # Khởi tạo Tkinter
    root = tk.Tk()
    app = App(root)
    
    # Xử lý Ctrl+C
    def _sigint_handler(sig, frame):
        try:
            app.append_log("🔔 Nhận Ctrl+C — dừng worker và thoát ứng dụng...")
        except Exception:
            print("Nhận Ctrl+C — dừng worker...")
        try:
            app.stop()
        except Exception:
            pass
        try:
            root.quit()
        except Exception:
            pass
    
    signal.signal(signal.SIGINT, _sigint_handler)
    
    # Chạy GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        _sigint_handler(None, None)

if __name__ == "__main__":
    main()
