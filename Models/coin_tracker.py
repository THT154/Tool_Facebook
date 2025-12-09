#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coin_tracker.py - Theo dõi và thống kê số xu kiếm được
"""
import os
import re
import json
from datetime import datetime, timedelta
from Models.config import APP_DIR

COINS_DATA_FILE = os.path.join(APP_DIR, "coins_data.txt")

class CoinTracker:
    """Theo dõi và thống kê xu"""
    
    def __init__(self):
        self.session_coins = 0  # Xu trong phiên hiện tại
        self.session_jobs = 0   # Số job thành công trong phiên
        self.data = self._load_data()
    
    def _load_data(self):
        """Load dữ liệu từ file"""
        if not os.path.exists(COINS_DATA_FILE):
            return []
        
        try:
            with open(COINS_DATA_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                data = []
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            data.append(entry)
                        except Exception:
                            pass
                return data
        except Exception:
            return []
    
    def _save_entry(self, coins, timestamp=None):
        """Lưu 1 entry vào file"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        entry = {
            'timestamp': timestamp,
            'coins': coins
        }
        
        try:
            with open(COINS_DATA_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            self.data.append(entry)
        except Exception as e:
            print(f"Lỗi lưu coins data: {e}")
    
    def add_coins(self, coins):
        """Thêm xu vào session và lưu vào file"""
        if coins > 0:
            self.session_coins += coins
            self.session_jobs += 1
            self._save_entry(coins)
    
    def reset_session(self):
        """Reset session (khi bắt đầu chạy mới)"""
        self.session_coins = 0
        self.session_jobs = 0
    
    def get_session_stats(self):
        """Lấy thống kê phiên hiện tại"""
        return {
            'coins': self.session_coins,
            'jobs': self.session_jobs
        }
    
    def get_today_stats(self):
        """Lấy thống kê hôm nay"""
        today = datetime.now().date()
        coins = 0
        jobs = 0
        
        for entry in self.data:
            try:
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts.date() == today:
                    coins += entry['coins']
                    jobs += 1
            except Exception:
                pass
        
        return {'coins': coins, 'jobs': jobs}
    
    def get_week_stats(self):
        """Lấy thống kê tuần này (7 ngày gần nhất)"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        coins = 0
        jobs = 0
        
        for entry in self.data:
            try:
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts >= week_ago:
                    coins += entry['coins']
                    jobs += 1
            except Exception:
                pass
        
        return {'coins': coins, 'jobs': jobs}
    
    def get_month_stats(self):
        """Lấy thống kê tháng này (30 ngày gần nhất)"""
        now = datetime.now()
        month_ago = now - timedelta(days=30)
        coins = 0
        jobs = 0
        
        for entry in self.data:
            try:
                ts = datetime.fromisoformat(entry['timestamp'])
                if ts >= month_ago:
                    coins += entry['coins']
                    jobs += 1
            except Exception:
                pass
        
        return {'coins': coins, 'jobs': jobs}
    
    def get_all_time_stats(self):
        """Lấy thống kê tổng cộng"""
        coins = sum(entry['coins'] for entry in self.data)
        jobs = len(self.data)
        return {'coins': coins, 'jobs': jobs}

def extract_coins_from_text(text):
    """
    Trích xuất số xu từ text
    Ví dụ: "Số xu 56 - Đã gửi thông tin..." -> 56
    """
    if not text:
        return 0
    
    # Tìm pattern "Số xu XX" hoặc "số xu XX"
    patterns = [
        r'[Ss]ố\s+xu\s+(\d+)',
        r'xu\s+(\d+)',
        r'(\d+)\s+xu',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                pass
    
    return 0

# Global instance
_coin_tracker = None

def get_coin_tracker():
    """Lấy coin tracker instance (singleton)"""
    global _coin_tracker
    if _coin_tracker is None:
        _coin_tracker = CoinTracker()
    return _coin_tracker
