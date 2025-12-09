#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_templates.py - Kiểm tra xem templates có được load đúng không
"""
import os
import json

def test_templates():
    """Kiểm tra templates trong settings.json"""
    
    settings_path = "settings.json"
    
    # Đọc settings
    if not os.path.exists(settings_path):
        print("❌ Không tìm thấy settings.json")
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc settings.json: {e}")
        return False
    
    # Kiểm tra templates
    templates = settings.get('templates', {})
    
    if not templates:
        print("❌ Không có templates nào trong settings.json")
        return False
    
    print(f"📁 Tìm thấy {len(templates)} templates trong settings:")
    print("=" * 60)
    
    valid_count = 0
    invalid_count = 0
    
    for key, path in templates.items():
        if os.path.exists(path):
            print(f"✅ {key:<25} -> {os.path.basename(path)}")
            valid_count += 1
        else:
            print(f"❌ {key:<25} -> {path} (FILE NOT FOUND)")
            invalid_count += 1
    
    print("=" * 60)
    print(f"📊 Kết quả: {valid_count} hợp lệ, {invalid_count} không tìm thấy file")
    
    if invalid_count == 0:
        print("🎉 Tất cả templates đều hợp lệ! Ứng dụng sẽ load được templates.")
        return True
    else:
        print("⚠️ Có một số templates không tìm thấy file. Cần kiểm tra lại.")
        return False

if __name__ == "__main__":
    print("🔍 Đang kiểm tra templates...")
    test_templates()