#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_template_paths.py - Test đường dẫn templates sau khi chuyển đổi
"""
import os
from Models.config import load_settings, get_template_path, APP_DIR

def test_template_paths():
    """Test tất cả đường dẫn template"""
    print("🧪 Đang test đường dẫn templates...")
    print(f"📁 APP_DIR: {APP_DIR}")
    
    settings = load_settings()
    if 'templates' not in settings:
        print("❌ Không tìm thấy templates trong settings")
        return False
    
    templates = settings['templates']
    print(f"📊 Tổng số templates: {len(templates)}")
    
    success_count = 0
    fail_count = 0
    
    for key, relative_path in templates.items():
        print(f"\n🔍 Test template: {key}")
        print(f"   Đường dẫn tương đối: {relative_path}")
        
        # Test với hàm get_template_path
        absolute_path = get_template_path(relative_path)
        print(f"   Đường dẫn tuyệt đối: {absolute_path}")
        
        if os.path.exists(absolute_path):
            print(f"   ✅ OK - File tồn tại")
            success_count += 1
        else:
            print(f"   ❌ FAIL - File không tồn tại")
            fail_count += 1
    
    print(f"\n📊 KẾT QUẢ:")
    print(f"   ✅ Thành công: {success_count}")
    print(f"   ❌ Thất bại: {fail_count}")
    print(f"   📈 Tỷ lệ thành công: {success_count/(success_count+fail_count)*100:.1f}%")
    
    return fail_count == 0

if __name__ == "__main__":
    success = test_template_paths()
    if success:
        print("\n🎉 Tất cả templates đều hoạt động tốt!")
        print("✅ Bây giờ bạn có thể copy project sang thiết bị khác mà không lo lỗi template.")
    else:
        print("\n❌ Có một số templates bị lỗi. Vui lòng kiểm tra lại.")