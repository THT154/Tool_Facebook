#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra paths sau khi refactor MVC
"""
import os
from Models.config import APP_DIR, TEMPLATES_DIR, SETTINGS_PATH

print("=" * 60)
print("🔍 KIỂM TRA PATHS SAU KHI REFACTOR MVC")
print("=" * 60)

print(f"\n📁 APP_DIR (Root):")
print(f"   {APP_DIR}")
print(f"   Exists: {os.path.exists(APP_DIR)}")

print(f"\n📁 TEMPLATES_DIR:")
print(f"   {TEMPLATES_DIR}")
print(f"   Exists: {os.path.exists(TEMPLATES_DIR)}")

if os.path.exists(TEMPLATES_DIR):
    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.png')]
    print(f"   Templates found: {len(templates)}")
    if templates:
        print(f"   Sample: {templates[:3]}")

print(f"\n📁 SETTINGS_PATH:")
print(f"   {SETTINGS_PATH}")
print(f"   Exists: {os.path.exists(SETTINGS_PATH)}")

print(f"\n📁 Models/ (Data files):")
models_dir = os.path.join(APP_DIR, "Models")
print(f"   {models_dir}")
print(f"   Exists: {os.path.exists(models_dir)}")

if os.path.exists(models_dir):
    data_files = [f for f in os.listdir(models_dir) if f.endswith('.txt')]
    print(f"   Data files: {data_files}")

print(f"\n📁 Controllers/:")
controllers_dir = os.path.join(APP_DIR, "Controllers")
print(f"   {controllers_dir}")
print(f"   Exists: {os.path.exists(controllers_dir)}")

if os.path.exists(controllers_dir):
    controllers = [f for f in os.listdir(controllers_dir) if f.endswith('.py')]
    print(f"   Controllers: {len(controllers)}")
    print(f"   Files: {controllers}")

print(f"\n📁 Utils/:")
utils_dir = os.path.join(APP_DIR, "Utils")
print(f"   {utils_dir}")
print(f"   Exists: {os.path.exists(utils_dir)}")

if os.path.exists(utils_dir):
    utils = [f for f in os.listdir(utils_dir) if f.endswith('.py')]
    print(f"   Utils: {len(utils)}")
    print(f"   Files: {utils}")

print("\n" + "=" * 60)
print("✅ KIỂM TRA HOÀN TẤT")
print("=" * 60)

# Test import
print("\n🔧 Test imports...")
try:
    from Controllers.sequence_worker import SequenceWorker
    print("   ✅ Controllers.sequence_worker")
except Exception as e:
    print(f"   ❌ Controllers.sequence_worker: {e}")

try:
    from Models.coin_tracker import get_coin_tracker
    print("   ✅ Models.coin_tracker")
except Exception as e:
    print(f"   ❌ Models.coin_tracker: {e}")

try:
    from Utils.adb_utils import ADBController
    print("   ✅ Utils.adb_utils")
except Exception as e:
    print(f"   ❌ Utils.adb_utils: {e}")

try:
    from Utils.image_utils import load_gray
    print("   ✅ Utils.image_utils")
except Exception as e:
    print(f"   ❌ Utils.image_utils: {e}")

print("\n✅ Tất cả imports thành công!")
