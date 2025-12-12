#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_account_management.py - Test hệ thống quản lý tài khoản blocked/max job
"""
import os
import datetime

def test_account_files():
    """Test các file quản lý tài khoản"""
    print("🧪 Test hệ thống quản lý tài khoản...")
    
    files_to_check = [
        {
            'path': 'Models/blocked_accounts.txt',
            'description': 'Tài khoản bị blocked',
            'type': 'permanent'
        },
        {
            'path': 'Models/max_job_accounts.txt',
            'description': 'Tài khoản max job',
            'type': 'daily_reset'
        },
        {
            'path': 'Models/last_reset_date.txt',
            'description': 'Ngày reset cuối',
            'type': 'date_tracker'
        }
    ]
    
    all_good = True
    
    for file_info in files_to_check:
        file_path = file_info['path']
        print(f"\n🔍 Kiểm tra: {file_info['description']}")
        print(f"   📁 File: {file_path}")
        
        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
            print(f"   ❌ File không tồn tại!")
            all_good = False
            continue
        
        # Kiểm tra quyền đọc
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   ✅ Đọc file: OK")
        except Exception as e:
            print(f"   ❌ Lỗi đọc file: {e}")
            all_good = False
            continue
        
        # Kiểm tra quyền ghi
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                pass
            print(f"   ✅ Ghi file: OK")
        except Exception as e:
            print(f"   ❌ Lỗi ghi file: {e}")
            all_good = False
            continue
        
        # Kiểm tra nội dung theo loại file
        if file_info['type'] == 'date_tracker':
            try:
                date_str = content.strip()
                datetime.datetime.fromisoformat(date_str)
                print(f"   ✅ Format ngày: OK ({date_str})")
            except:
                print(f"   ❌ Format ngày không hợp lệ: {content.strip()}")
                all_good = False
        else:
            print(f"   ✅ Nội dung: {len(content)} ký tự")
    
    return all_good

def test_account_operations():
    """Test các thao tác với tài khoản"""
    print(f"\n🔧 Test thao tác với tài khoản...")
    
    # Test thêm tài khoản blocked
    test_account = "999_999"
    blocked_file = "Models/blocked_accounts.txt"
    
    try:
        # Đọc nội dung hiện tại
        with open(blocked_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Thêm tài khoản test
        with open(blocked_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{test_account}")
        
        # Kiểm tra đã thêm thành công
        with open(blocked_file, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        if test_account in new_content:
            print(f"   ✅ Thêm tài khoản blocked: OK")
        else:
            print(f"   ❌ Thêm tài khoản blocked: FAIL")
            return False
        
        # Khôi phục nội dung gốc
        with open(blocked_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"   ✅ Khôi phục file: OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test thao tác: {e}")
        return False

def main():
    """Chạy tất cả test"""
    print("🚀 TEST HỆ THỐNG QUẢN LÝ TÀI KHOẢN")
    print("=" * 50)
    
    # Test 1: Kiểm tra file
    files_ok = test_account_files()
    
    # Test 2: Kiểm tra thao tác
    operations_ok = test_account_operations()
    
    print(f"\n" + "=" * 50)
    print(f"📊 KẾT QUẢ TỔNG HỢP:")
    print(f"   ✅ File system: {'OK' if files_ok else 'FAIL'}")
    print(f"   ✅ Operations: {'OK' if operations_ok else 'FAIL'}")
    
    if files_ok and operations_ok:
        print(f"\n🎉 Hệ thống quản lý tài khoản hoạt động tốt!")
        print(f"✅ Sẵn sàng để sử dụng AccountSwitcher")
        return True
    else:
        print(f"\n❌ Có vấn đề với hệ thống quản lý tài khoản")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)