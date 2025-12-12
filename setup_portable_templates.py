#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_portable_templates.py - Setup templates portable cho mọi thiết bị
"""
import os
import sys

def main():
    """Chạy tất cả các bước setup templates portable"""
    print("🚀 SETUP TEMPLATES PORTABLE")
    print("=" * 50)
    
    steps = [
        ("1️⃣ Khởi tạo các file dữ liệu cần thiết", "init_data_files.py"),
        ("2️⃣ Đăng ký templates với đường dẫn tương đối", "auto_register_templates.py"),
        ("3️⃣ Chuyển đổi settings cũ (nếu có)", "convert_template_paths.py"),
        ("4️⃣ Test tất cả templates", "test_template_paths.py")
    ]
    
    for step_name, script_name in steps:
        print(f"\n{step_name}")
        print("-" * 40)
        
        if not os.path.exists(script_name):
            print(f"❌ Không tìm thấy {script_name}")
            continue
            
        try:
            # Import và chạy script
            if script_name == "init_data_files.py":
                from init_data_files import init_data_files
                success = init_data_files()
            elif script_name == "auto_register_templates.py":
                from auto_register_templates import auto_register_templates
                success = auto_register_templates()
            elif script_name == "convert_template_paths.py":
                from convert_template_paths import convert_template_paths
                success = convert_template_paths()
            elif script_name == "test_template_paths.py":
                from test_template_paths import test_template_paths
                success = test_template_paths()
            else:
                success = False
                
            if not success:
                print(f"❌ Lỗi khi chạy {script_name}")
                return False
                
        except Exception as e:
            print(f"❌ Exception khi chạy {script_name}: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 HOÀN TẤT SETUP!")
    print("✅ Templates đã được setup thành công")
    print("✅ Bây giờ bạn có thể:")
    print("   - Copy project sang thiết bị khác")
    print("   - Chạy trên Windows/Mac/Linux")
    print("   - Không lo lỗi đường dẫn template")
    print("   - Hệ thống quản lý tài khoản blocked/max job hoạt động")
    print("\n📖 Xem thêm: TEMPLATE_MIGRATION_GUIDE.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)