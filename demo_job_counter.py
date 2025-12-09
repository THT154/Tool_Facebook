#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_job_counter.py - Demo job completion counter với tất cả tính năng
"""
import tkinter as tk
import time
import threading
import random

# Import GUI class
from gui import App

def demo_job_counter():
    """Demo job completion counter với realistic simulation"""
    root = tk.Tk()
    app = App(root)
    
    # Simulate realistic job processing
    def simulate_realistic_jobs():
        # Đợi GUI load xong
        time.sleep(3)
        print("🚀 Bắt đầu simulation...")
        
        # Simulate 20 jobs với thời gian thực tế
        for i in range(20):
            if i == 0:
                print("📊 Bắt đầu session - Reset counter")
                try:
                    app.reset_completed_jobs_counter()
                except Exception as e:
                    print(f"⚠️ Lỗi reset counter: {e}")
                    continue
            
            # Job attempt
            app.increment_job_attempts()
            print(f"🎯 Job {i+1}: Bắt đầu xử lý...")
            
            # Simulate job processing time (2-5 seconds)
            processing_time = random.uniform(2, 5)
            time.sleep(processing_time)
            
            # Simulate success rate ~80%
            success = random.random() < 0.8
            
            if success:
                app.increment_completed_jobs()
                print(f"  ✅ Job {i+1}: Hoàn thành thành công!")
            else:
                print(f"  ❌ Job {i+1}: Thất bại")
            
            # Pause between jobs
            time.sleep(random.uniform(0.5, 1.5))
        
        print("🏁 Simulation hoàn tất!")
    
    # Chạy simulation trong thread riêng
    thread = threading.Thread(target=simulate_realistic_jobs, daemon=True)
    thread.start()
    
    # Chạy GUI
    root.mainloop()

if __name__ == "__main__":
    print("🎮 Demo Job Completion Counter")
    print("=" * 50)
    print("Tính năng:")
    print("✅ Đếm job hoàn thành")
    print("📊 Tỷ lệ thành công (%)")
    print("⚡ Tốc độ job/phút")
    print("🕒 Thời gian thực")
    print("=" * 50)
    demo_job_counter()