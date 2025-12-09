#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
job_detector.py - Phát hiện và xử lý các loại job icons
"""
import os
import time
import random
from Utils.image_utils import load_gray, locate_template
from Utils.window_utils import click_at, get_ldplayer_window

class JobDetector:
    """Class xử lý phát hiện và click các loại job icons"""
    
    def __init__(self, templates, params, log_fn=None):
        self.templates = templates
        self.params = params
        self.log_fn = log_fn or (lambda m: None)
    
    def find_and_click_job_icons(self, retries_per_template=4, timeout_per_try=None):
        """
        Tìm và click job icon
        Hỗ trợ nhiều loại: job_heart, job_like, job_cmt, job_share, job_follow, job_icon*
        """
        if timeout_per_try is None:
            timeout_per_try = float(self.params.get('timeout_job', 8.0))
        
        candidates = self._get_job_icon_candidates()
        
        if not candidates:
            return None
        
        for key in candidates:
            path = self.templates.get(key)
            if not path or not os.path.exists(path):
                continue
            
            result = self._try_find_template(key, path, retries_per_template, timeout_per_try)
            if result is not None:
                return result
        
        return None
    
    def _get_job_icon_candidates(self):
        """Lấy danh sách các template key có thể là job icon"""
        candidates = []
        
        # Các loại job phổ biến
        common = ['job_heart', 'job_like', 'job_cmt', 'job_comment', 'job_share', 'job_follow']
        for k in common:
            if k in self.templates:
                candidates.append(k)
        
        # Các job_icon* và job_* khác
        for k in list(self.templates.keys()):
            kl = k.lower()
            if kl.startswith('job_icon') or kl.startswith('job_') or (kl.startswith('job') and 'icon' in kl):
                if k not in candidates:
                    candidates.append(k)
        
        # Extras
        for extra in ('job', 'jobicon'):
            if extra in self.templates and extra not in candidates:
                candidates.append(extra)
        
        return candidates
    
    def _try_find_template(self, key, path, retries, timeout_per_try):
        """Thử tìm một template cụ thể"""
        try:
            tmpl = load_gray(path)
        except Exception as e:
            self.log_fn(f"Job-detect: không thể load template '{key}': {e}")
            return None
        
        for attempt in range(retries):
            # Kiểm tra ADB mode
            from Utils.window_utils import is_adb_mode
            
            regions = []
            
            if is_adb_mode():
                # ADB mode: Screenshot đã là toàn bộ LDPlayer, không cần region
                regions.append(None)
            else:
                # Pyautogui mode: Cần region của LDPlayer window
                ld = get_ldplayer_window()
                if ld:
                    left, top, w, h, _ = ld
                    regions.append((left, top, w, h))
                regions.append(None)
            
            for region in regions:
                try:
                    conf = float(self.params.get('conf_job', 0.85))
                    res = locate_template(
                        tmpl, confidence=conf, 
                        timeout=min(1.2, timeout_per_try), 
                        step=0.06, region=region
                    )
                    
                    if res is not None:
                        x, y, score = res
                        self.log_fn(f"Job-detect: Tìm thấy '{key}' (score={score:.2f}) -> click")
                        click_at(x, y)
                        time.sleep(random.uniform(1.2, 2.0))
                        return (key, int(x), int(y), float(score))
                except Exception as e:
                    self.log_fn(f"Job-detect: lỗi khi tìm '{key}' trong region {region}: {e}")
            
            time.sleep(0.04)
        
        return None
    
    def try_click_optional_templates(self, keys, timeout_per_try=1.0, retries=3, conf_key='conf_job'):
        """
        Thử click các template optional (như copy button)
        Returns: True nếu tìm thấy và click, False nếu không
        """
        for key in keys:
            path = self.templates.get(key)
            if not path or not os.path.exists(path):
                continue
            
            try:
                tmpl = load_gray(path)
            except Exception as e:
                self.log_fn(f"Optional-click: không thể load template '{key}': {e}")
                continue
            
            for attempt in range(retries):
                # Kiểm tra ADB mode
                from Utils.window_utils import is_adb_mode
                
                regions = []
                
                if is_adb_mode():
                    # ADB mode: Screenshot đã là toàn bộ LDPlayer, không cần region
                    regions.append(None)
                else:
                    # Pyautogui mode: Cần region của LDPlayer window
                    ld = get_ldplayer_window()
                    if ld:
                        left, top, w, h, _ = ld
                        regions.append((left, top, w, h))
                    regions.append(None)
                
                for region in regions:
                    try:
                        conf = float(self.params.get(conf_key, 0.85))
                        res = locate_template(
                            tmpl, confidence=conf, 
                            timeout=min(1.2, timeout_per_try), 
                            step=0.06, region=region
                        )
                        
                        if res is not None:
                            x, y, score = res
                            self.log_fn(f"Optional-click: Tìm thấy '{key}' (score={score:.2f}) -> click")
                            click_at(x, y)
                            time.sleep(random.uniform(0.5, 0.9))
                            return True
                    except Exception as e:
                        self.log_fn(f"Optional-click: lỗi khi tìm '{key}' in region {region}: {e}")
                
                time.sleep(0.04)
        
        return False
