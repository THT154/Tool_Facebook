#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_template_paths.py - Chuyển đổi đường dẫn templates từ tuyệt đối sang tương đối
"""
import os
import json
from Models.config import SETTINGS_PATH, APP_DIR

def convert_template_paths():
    """Chuyển đổi tất cả đường dẫn template từ tuyệt đối sang tương đối"""
    
    if not os.path.exists(SETTINGS_PATH):
        print("❌ Không tìm thấy file settings.json")
        return False
    
    # Đọc settings hiện tại
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc settings: {e}")
        return False
    
    if 'templates' not in settings:
        print("❌ Không tìm thấy section templates trong settings")
        return False
    
    # Chuyển đổi đường dẫn
    converted_count = 0
    for key, path in settings['templates'].items():
        if os.path.isabs(path):
            try:
                # Chuyển thành đường dẫn tương đối
                rel_path = os.path.relpath(path, APP_DIR)
                settings['templates'][key] = rel_path
                converted_count += 1
                print(f"✓ Chuyển đổi: {key}")
                print(f"  Từ: {path}")
                print(f"  Thành: {rel_path}")
            except Exception as e:
                print(f"❌ Lỗi khi chuyển đổi {key}: {e}")
    
    if converted_count == 0:
        print("✅ Tất cả đường dẫn đã là tương đối rồi!")
        return True
    
    # Lưu lại settings
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Đã chuyển đổi {converted_count} đường dẫn template thành tương đối")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi lưu settings: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Đang chuyển đổi đường dẫn templates...")
    success = convert_template_paths()
    if success:
        print("🎉 Hoàn tất! Bây giờ templates sẽ hoạt động trên mọi thiết bị.")
    else:
        print("❌ Có lỗi xảy ra. Vui lòng kiểm tra lại.")