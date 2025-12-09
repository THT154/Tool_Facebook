#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_job_counter.py - Test job completion counter
"""
import tkinter as tk
import time
import threading

# Import GUI class
from gui import App

def test_counter():
    """Test job completion counter"""
    root = tk.Tk()
    app = App(root)
    
    # Đợi GUI load xong
    time.sleep(2)
    
    # Test increment counter
    def simulate_jobs():
        for i in range(8):
            time.sleep(1)
            app.increment_job_attempts()
            print(f"Simulated job {i+1} attempt")
            
            # Simulate success rate ~75%
            if i % 4 != 0:  # 3 out of 4 jobs succeed
                time.sleep(0.5)
                app.increment_completed_jobs()
                print(f"  -> Job {i+1} completed successfully")
            else:
                print(f"  -> Job {i+1} failed")
    
    # Chạy simulation trong thread riêng
    thread = threading.Thread(target=simulate_jobs, daemon=True)
    thread.start()
    
    # Chạy GUI
    root.mainloop()

if __name__ == "__main__":
    print("🧪 Testing job completion counter...")
    test_counter()