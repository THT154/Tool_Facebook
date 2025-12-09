#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ocr_utils.py - OCR để đọc text từ màn hình
"""
import cv2
import numpy as np

# Thử import pytesseract (optional)
try:
    import pytesseract
    
    # Cấu hình path cho Tesseract (Windows)
    import os
    import platform
    
    if platform.system() == 'Windows':
        # Thử các đường dẫn phổ biến
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Thử import easyocr (optional)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    _easyocr_reader = None
except ImportError:
    EASYOCR_AVAILABLE = False

def get_easyocr_reader():
    """Lấy EasyOCR reader (singleton)"""
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        try:
            _easyocr_reader = easyocr.Reader(['vi', 'en'], gpu=False)
        except Exception:
            pass
    return _easyocr_reader

def preprocess_for_ocr(img):
    """
    Tiền xử lý ảnh cho OCR
    - Convert sang grayscale
    - Tăng contrast
    - Threshold
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Tăng contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Threshold
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary

def ocr_with_tesseract(img, lang='eng'):
    """
    OCR bằng Tesseract
    Returns: text string hoặc None
    """
    if not TESSERACT_AVAILABLE:
        return None
    
    try:
        # Preprocess
        processed = preprocess_for_ocr(img)
        
        # OCR với config tối ưu cho text ngắn (tên tài khoản)
        # PSM 7: Treat the image as a single text line
        custom_config = r'--oem 3 --psm 7'
        text = pytesseract.image_to_string(processed, lang=lang, config=custom_config)
        return text.strip()
    except Exception as e:
        # Không log nữa để tránh spam
        return None

def ocr_with_easyocr(img):
    """
    OCR bằng EasyOCR
    Returns: text string hoặc None
    """
    if not EASYOCR_AVAILABLE:
        return None
    
    try:
        reader = get_easyocr_reader()
        if reader is None:
            return None
        
        # Preprocess
        processed = preprocess_for_ocr(img)
        
        # OCR
        results = reader.readtext(processed, detail=0)
        text = ' '.join(results)
        return text.strip()
    except Exception as e:
        print(f"Lỗi EasyOCR: {e}")
        return None

def ocr_simple_digits(img):
    """
    OCR đơn giản chỉ cho số (không cần thư viện OCR)
    Dùng template matching với các chữ số 0-9
    Returns: số hoặc None
    """
    # TODO: Implement simple digit recognition nếu không có OCR library
    return None

def extract_text_from_image(img, method='auto', prefer_easyocr=True):
    """
    Trích xuất text từ ảnh
    
    Args:
        img: numpy array (BGR hoặc grayscale)
        method: 'auto', 'tesseract', 'easyocr', 'simple'
        prefer_easyocr: Ưu tiên EasyOCR (tốt hơn cho tiếng Việt)
    
    Returns:
        text string hoặc None
    """
    if method == 'auto':
        # ƯU TIÊN EasyOCR (tốt hơn cho tiếng Việt)
        if prefer_easyocr and EASYOCR_AVAILABLE:
            text = ocr_with_easyocr(img)
            if text:
                return text
        
        # Thử Tesseract (nếu EasyOCR thất bại)
        if TESSERACT_AVAILABLE:
            text = ocr_with_tesseract(img)
            if text:
                return text
        
        # Thử EasyOCR nếu chưa thử
        if not prefer_easyocr and EASYOCR_AVAILABLE:
            text = ocr_with_easyocr(img)
            if text:
                return text
        
        # Fallback: simple digits
        return ocr_simple_digits(img)
    
    elif method == 'tesseract':
        return ocr_with_tesseract(img)
    
    elif method == 'easyocr':
        return ocr_with_easyocr(img)
    
    elif method == 'simple':
        return ocr_simple_digits(img)
    
    return None

def check_ocr_available():
    """Kiểm tra OCR có sẵn không"""
    return TESSERACT_AVAILABLE or EASYOCR_AVAILABLE

def get_ocr_method():
    """Lấy phương thức OCR khả dụng (ưu tiên EasyOCR)"""
    if EASYOCR_AVAILABLE:
        return 'easyocr'
    elif TESSERACT_AVAILABLE:
        return 'tesseract'
    else:
        return 'none'

def init_easyocr():
    """Khởi tạo EasyOCR reader trước (để tránh lag lần đầu)"""
    if EASYOCR_AVAILABLE:
        try:
            reader = get_easyocr_reader()
            if reader:
                print("✓ EasyOCR đã sẵn sàng (hỗ trợ tiếng Việt)")
                return True
        except Exception as e:
            print(f"⚠️ Lỗi khi khởi tạo EasyOCR: {e}")
    return False
