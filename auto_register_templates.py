#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_register_templates.py - Tự động đăng ký tất cả templates có sẵn
"""
import os
import json

def auto_register_templates():
    """Tự động đăng ký tất cả templates có sẵn trong folder templates/"""
    
    # Đường dẫn
    templates_dir = "templates"
    settings_path = "settings.json"
    
    # Đọc settings hiện tại
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception as e:
            print(f"Lỗi khi đọc settings: {e}")
            return False
    
    # Khởi tạo templates dict nếu chưa có
    if 'templates' not in settings:
        settings['templates'] = {}
    
    # Mapping tên file -> key template
    file_to_key_mapping = {
        'job_icon.png': 'job_icon',
        'job_heart.png': 'job_heart', 
        'job_like.png': 'job_like',
        'job_cmt.png': 'job_cmt',
        'job_share.png': 'job_share',
        'job_follow.png': 'job_follow',
        'complete_icon.png': 'complete_icon',
        'fail_icon.png': 'fail_icon',
        'fail_button.png': 'fail_button',
        'ok_button.png': 'ok_button',
        'confirm_button.png': 'confirm_button',
        'copy_button.png': 'copy_button',
        'fb_icon.png': 'fb_icon',
        'golike_icon.png': 'golike_icon',
        'ld_golike_icon.png': 'ld_golike_icon',
        'home_button.png': 'home_button',
        'category_button.png': 'category_button',
        'earn_button.png': 'earn_button',
        'earn_page_header.png': 'earn_page_header',
        'max_job_popup.png': 'max_job_popup',
        'blocked_account_popup.png': 'blocked_account_popup',
        'account_selector.png': 'account_selector',
        'current_account_red.png': 'current_account_red',
        'account_item.png': 'account_item',
        "Header 'Kiếm thưởng.png": 'earn_page_header_alt'
    }
    
    # Quét folder templates và đăng ký
    registered_count = 0
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                file_path = os.path.join(templates_dir, filename)
                
                # Tìm key tương ứng
                template_key = file_to_key_mapping.get(filename)
                if not template_key:
                    # Tạo key từ tên file (loại bỏ extension và thay thế ký tự đặc biệt)
                    template_key = os.path.splitext(filename)[0].lower()
                    template_key = template_key.replace(' ', '_').replace("'", '').replace('"', '')
                
                # Đăng ký template
                settings['templates'][template_key] = os.path.abspath(file_path)
                registered_count += 1
                print(f"✓ Đăng ký: {filename} -> {template_key}")
    
    # Lưu settings
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Đã đăng ký {registered_count} templates vào settings.json")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi lưu settings: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Đang tự động đăng ký templates...")
    success = auto_register_templates()
    if success:
        print("🎉 Hoàn tất! Bây giờ bạn có thể chạy ứng dụng và sẽ thấy các templates đã được load.")
    else:
        print("❌ Có lỗi xảy ra. Vui lòng kiểm tra lại.")