#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_data_files.py - Khởi tạo tất cả các file dữ liệu cần thiết
"""
import os
import datetime
from Models.config import ensure_directories

def init_data_files():
    """Khởi tạo tất cả các file dữ liệu cần thiết"""
    print("🔧 Đang khởi tạo các file dữ liệu...")
    
    # Đảm bảo thư mục Models tồn tại
    ensure_directories()
    
    # Danh sách các file cần tạo
    files_to_create = [
        {
            'path': 'Models/blocked_accounts.txt',
            'content': '''# File lưu trữ tài khoản bị blocked vĩnh viễn
# Format: một tài khoản mỗi dòng (ví dụ: 273_265)
# File này sẽ không bị reset tự động
''',
            'description': 'Tài khoản bị blocked (vĩnh viễn)'
        },
        {
            'path': 'Models/max_job_accounts.txt', 
            'content': '''# File lưu trữ tài khoản đã max job trong ngày
# Format: một tài khoản mỗi dòng (ví dụ: 273_484)
# File này sẽ được reset tự động mỗi ngày mới
''',
            'description': 'Tài khoản max job (reset mỗi ngày)'
        },
        {
            'path': 'Models/last_reset_date.txt',
            'content': datetime.date.today().isoformat(),
            'description': 'Ngày reset cuối cùng'
        }
    ]
    
    created_count = 0
    
    for file_info in files_to_create:
        file_path = file_info['path']
        
        if os.path.exists(file_path):
            print(f"✓ {file_info['description']}: {file_path} (đã tồn tại)")
        else:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                print(f"✅ Tạo mới: {file_info['description']}: {file_path}")
                created_count += 1
            except Exception as e:
                print(f"❌ Lỗi khi tạo {file_path}: {e}")
                return False
    
    print(f"\n📊 Kết quả:")
    print(f"   ✅ Đã tạo {created_count} file mới")
    print(f"   📁 Tổng cộng {len(files_to_create)} file cần thiết")
    
    # Kiểm tra quyền ghi
    print(f"\n🔍 Kiểm tra quyền ghi...")
    for file_info in files_to_create:
        file_path = file_info['path']
        try:
            # Test ghi file
            with open(file_path, 'a', encoding='utf-8') as f:
                pass
            print(f"✓ {file_path}: OK")
        except Exception as e:
            print(f"❌ {file_path}: Lỗi - {e}")
            return False
    
    print(f"\n🎉 Hoàn tất khởi tạo!")
    print(f"✅ Tất cả file dữ liệu đã sẵn sàng")
    return True

if __name__ == "__main__":
    success = init_data_files()
    if success:
        print("\n📖 Hướng dẫn sử dụng:")
        print("   - blocked_accounts.txt: Thêm tài khoản bị block vĩnh viễn")
        print("   - max_job_accounts.txt: Tự động quản lý bởi hệ thống")
        print("   - last_reset_date.txt: Tự động cập nhật mỗi ngày")
    else:
        print("\n❌ Có lỗi xảy ra khi khởi tạo file dữ liệu")