#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py - Quản lý cấu hình và settings
"""
import os
import json

# APP_DIR là thư mục gốc của project (parent của Models/)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

# ADB Configuration
DEFAULT_ADB_PATH = "adb"  # Hoặc đường dẫn đầy đủ: "C:\\path\\to\\adb.exe"
DEFAULT_ADB_PORT = 5555  # Port mặc định của LDPlayer

def ensure_directories():
    """Tạo thư mục cần thiết nếu chưa có"""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

def load_settings():
    """Đọc settings từ file JSON"""
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings_dict):
    """Lưu settings vào file JSON"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu settings: {e}")
        return False
