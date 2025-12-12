#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_from_templates.py - Khởi tạo project từ các file template
Script này sẽ copy các file .template thành file thực để project hoạt động
"""
import os
import shutil
import datetime

def setup_from_templates():
    """Copy các file template thành file thực"""
    print("🔧 Khởi tạo project từ templates...")
    
    # Danh sách file template cần copy
    template_files = [
        {
            'template': 'Models/blocked_accounts.txt.template',
            'target': 'Models/blocked_accounts.txt',
            'description': 'Tài khoản bị blocked'
        },
        {
            'template': 'Models/max_job_accounts.txt.template', 
            'target': 'Models/max_job_accounts.txt',
            'description': 'Tài khoản max job'
        },
        {
            'template': 'Models/last_reset_date.txt.template',
            'target': 'Models/last_reset_date.txt',
            'description': 'Ngày reset cuối',
            'update_content': True  # Cập nhật ngày hiện tại
        },
        {
            'template': 'settings.json.template',
            'target': 'settings.json', 
            'description': 'Cấu hình chính'
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for file_info in template_files:
        template_path = file_info['template']
        target_path = file_info['target']
        description = file_info['description']
        
        print(f"\n📁 {description}")
        print(f"   Template: {template_path}")
        print(f"   Target: {target_path}")
        
        # Kiểm tra template tồn tại
        if not os.path.exists(template_path):
            print(f"   ❌ Template không tồn tại!")
            continue
        
        # Kiểm tra target đã tồn tại chưa
        if os.path.exists(target_path):
            print(f"   ⚠️ File đã tồn tại - Bỏ qua")
            skipped_count += 1
            continue
        
        try:
            # Copy file
            shutil.copy2(template_path, target_path)
            
            # Cập nhật nội dung nếu cần
            if file_info.get('update_content'):
                if 'last_reset_date' in target_path:
                    # Cập nhật ngày hiện tại
                    today = datetime.date.today().isoformat()
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(today)
                    print(f"   ✅ Tạo và cập nhật ngày: {today}")
                else:
                    print(f"   ✅ Tạo thành công")
            else:
                print(f"   ✅ Tạo thành công")
            
            created_count += 1
            
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
    
    print(f"\n📊 Kết quả:")
    print(f"   ✅ Tạo mới: {created_count} file")
    print(f"   ⚠️ Bỏ qua: {skipped_count} file (đã tồn tại)")
    print(f"   📁 Tổng cộng: {len(template_files)} file")
    
    if created_count > 0:
        print(f"\n🎉 Khởi tạo thành công!")
        print(f"✅ Project đã sẵn sàng để chạy")
        return True
    elif skipped_count == len(template_files):
        print(f"\n✅ Project đã được khởi tạo từ trước")
        return True
    else:
        print(f"\n❌ Có lỗi trong quá trình khởi tạo")
        return False

def main():
    """Chạy setup và hướng dẫn"""
    print("🚀 SETUP PROJECT TỪ TEMPLATES")
    print("=" * 50)
    
    success = setup_from_templates()
    
    if success:
        print(f"\n📖 Hướng dẫn tiếp theo:")
        print(f"   1. Chạy: python auto_register_templates.py")
        print(f"   2. Hoặc chạy: python setup_portable_templates.py")
        print(f"   3. Sau đó có thể chạy: python gui.py")
        print(f"\n💡 Lưu ý:")
        print(f"   - Các file .txt sẽ không được commit lên git")
        print(f"   - Khi clone project mới, chạy lại script này")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)