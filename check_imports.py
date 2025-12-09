#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra tất cả imports sau khi refactor MVC
"""
import os
import re

# Modules cần kiểm tra
OLD_MODULES = [
    'window_utils', 'image_utils', 'adb_utils', 'ocr_utils', 
    'navigation', 'ldplayer_manager', 'reset_navigation',
    'account_switcher', 'sequence_worker', 'ok_watcher', 
    'job_detector', 'config', 'coin_tracker'
]

# Mapping đúng
CORRECT_IMPORTS = {
    'window_utils': 'Utils.window_utils',
    'image_utils': 'Utils.image_utils',
    'adb_utils': 'Utils.adb_utils',
    'ocr_utils': 'Utils.ocr_utils',
    'navigation': 'Utils.navigation',
    'ldplayer_manager': 'Utils.ldplayer_manager',
    'reset_navigation': 'Controllers.reset_navigation',
    'account_switcher': 'Controllers.account_switcher',
    'sequence_worker': 'Controllers.sequence_worker',
    'ok_watcher': 'Controllers.ok_watcher',
    'job_detector': 'Controllers.job_detector',
    'config': 'Models.config',
    'coin_tracker': 'Models.coin_tracker',
}

def check_file(filepath):
    """Kiểm tra imports trong một file"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Tìm import statements
            for old_module in OLD_MODULES:
                # Pattern: from module import hoặc import module
                patterns = [
                    rf'from {old_module} import',
                    rf'import {old_module}',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line):
                        # Kiểm tra xem đã có prefix chưa
                        correct = CORRECT_IMPORTS[old_module]
                        if correct not in line:
                            issues.append({
                                'file': filepath,
                                'line': line_num,
                                'content': line.strip(),
                                'old': old_module,
                                'new': correct
                            })
    
    except Exception as e:
        print(f"⚠️ Lỗi khi đọc {filepath}: {e}")
    
    return issues

def main():
    print("=" * 70)
    print("🔍 KIỂM TRA IMPORTS SAU KHI REFACTOR MVC")
    print("=" * 70)
    
    all_issues = []
    
    # Kiểm tra tất cả file Python
    for root, dirs, files in os.walk('.'):
        # Bỏ qua __pycache__ và .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.vscode']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                issues = check_file(filepath)
                all_issues.extend(issues)
    
    if all_issues:
        print(f"\n❌ Tìm thấy {len(all_issues)} import chưa được cập nhật:\n")
        
        for issue in all_issues:
            print(f"📁 {issue['file']}:{issue['line']}")
            print(f"   ❌ {issue['content']}")
            print(f"   ✅ Nên sửa: from {issue['old']} → from {issue['new']}")
            print()
    else:
        print("\n✅ Tất cả imports đã được cập nhật đúng!")
        print("\n📊 Kiểm tra:")
        print(f"   - Controllers: {len([m for m in OLD_MODULES if 'Controllers' in CORRECT_IMPORTS.get(m, '')])}")
        print(f"   - Models: {len([m for m in OLD_MODULES if 'Models' in CORRECT_IMPORTS.get(m, '')])}")
        print(f"   - Utils: {len([m for m in OLD_MODULES if 'Utils' in CORRECT_IMPORTS.get(m, '')])}")
    
    print("\n" + "=" * 70)
    return len(all_issues)

if __name__ == '__main__':
    exit(main())
