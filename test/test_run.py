#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra xem code có chạy được không
"""
print("=" * 60)
print("🧪 TEST IMPORTS AFTER MVC REFACTOR")
print("=" * 60)

# Test 1: Import Controllers
print("\n1️⃣ Test Controllers...")
try:
    from Controllers.sequence_worker import SequenceWorker
    print("   ✅ sequence_worker")
except Exception as e:
    print(f"   ❌ sequence_worker: {e}")

try:
    from Controllers.account_switcher import AccountSwitcher
    print("   ✅ account_switcher")
except Exception as e:
    print(f"   ❌ account_switcher: {e}")

try:
    from Controllers.ok_watcher import OkWatcher
    print("   ✅ ok_watcher")
except Exception as e:
    print(f"   ❌ ok_watcher: {e}")

try:
    from Controllers.job_detector import JobDetector
    print("   ✅ job_detector")
except Exception as e:
    print(f"   ❌ job_detector: {e}")

try:
    from Controllers.reset_navigation import ResetNavigation
    print("   ✅ reset_navigation")
except Exception as e:
    print(f"   ❌ reset_navigation: {e}")

# Test 2: Import Models
print("\n2️⃣ Test Models...")
try:
    from Models.config import load_settings, save_settings
    print("   ✅ config")
except Exception as e:
    print(f"   ❌ config: {e}")

try:
    from Models.coin_tracker import get_coin_tracker
    print("   ✅ coin_tracker")
except Exception as e:
    print(f"   ❌ coin_tracker: {e}")

# Test 3: Import Utils
print("\n3️⃣ Test Utils...")
try:
    from Utils.adb_utils import ADBController
    print("   ✅ adb_utils")
except Exception as e:
    print(f"   ❌ adb_utils: {e}")

try:
    from Utils.window_utils import click_at
    print("   ✅ window_utils")
except Exception as e:
    print(f"   ❌ window_utils: {e}")

try:
    from Utils.image_utils import load_gray
    print("   ✅ image_utils")
except Exception as e:
    print(f"   ❌ image_utils: {e}")

try:
    from Utils.ocr_utils import extract_text_from_image
    print("   ✅ ocr_utils")
except Exception as e:
    print(f"   ❌ ocr_utils: {e}")

try:
    from Utils.navigation import press_back_method
    print("   ✅ navigation")
except Exception as e:
    print(f"   ❌ navigation: {e}")

try:
    from Utils.ldplayer_manager import LDPlayerManager
    print("   ✅ ldplayer_manager")
except Exception as e:
    print(f"   ❌ ldplayer_manager: {e}")

# Test 4: Test lazy imports trong JobDetector
print("\n4️⃣ Test lazy imports...")
try:
    detector = JobDetector({}, {}, lambda x: None)
    print("   ✅ JobDetector instantiation")
except Exception as e:
    print(f"   ❌ JobDetector: {e}")

print("\n" + "=" * 60)
print("✅ TEST HOÀN TẤT!")
print("=" * 60)
