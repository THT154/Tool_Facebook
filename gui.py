#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py - Giao diện người dùng Tkinter
"""
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from Models.config import load_settings, save_settings

class App:
    """Giao diện chính của ứng dụng"""
    
    def __init__(self, master):
        self.master = master
        master.title("🤖 Golike Sequence Bot")
        master.geometry("1000x700")
        master.resizable(True, True)
        
        # Show loading message
        loading_label = tk.Label(master, text="⏳ Đang tải...", 
                                font=('Arial', 14), fg='#666')
        loading_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Styling
        self._setup_styles()
        
        self.templates = {}
        self.jobs = []
        self.worker = None  # Lazy init
        self.settings = load_settings()
        
        # Create widgets sau khi hiển thị loading
        self.master.after(10, lambda: self._init_ui(loading_label))
    
    def _init_ui(self, loading_label):
        """Khởi tạo UI sau loading"""
        self._create_widgets()
        loading_label.destroy()
        
        # Load settings và init worker sau khi GUI đã hiển thị (async)
        self.master.after(100, self._lazy_init)
    
    def _setup_styles(self):
        """Thiết lập styles cho ttk widgets"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure('Start.TButton', 
                       background='#4CAF50', 
                       foreground='white',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        style.map('Start.TButton',
                 background=[('active', '#45a049')])
        
        style.configure('Stop.TButton',
                       background='#f44336',
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       padding=10)
        style.map('Stop.TButton',
                 background=[('active', '#da190b')])
        
        style.configure('Save.TButton',
                       background='#2196F3',
                       foreground='white',
                       font=('Arial', 10, 'bold'),
                       padding=10)
        style.map('Save.TButton',
                 background=[('active', '#0b7dda')])
        
        # Frame styles
        style.configure('Card.TFrame', background='#f5f5f5', relief='raised')
        
        # Label styles
        style.configure('Title.TLabel', font=('Arial', 11, 'bold'), foreground='#333')
        style.configure('Subtitle.TLabel', font=('Arial', 9), foreground='#666')
    
    def _create_widgets(self):
        """Tạo các widgets cho GUI"""
        # Main container
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Control buttons
        self._create_control_section(main_frame)
        
        # Middle section: Notebook and Log side by side
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left side: Notebook (tabs)
        self.notebook = ttk.Notebook(middle_frame)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Tab 1: Templates (với sub-tabs)
        templates_tab = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(templates_tab, text="📁 Templates")
        self._create_templates_tab(templates_tab)
        
        # Tab 2: Settings
        settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab, text="⚙️ Cấu hình")
        self._create_settings_tab(settings_tab)
        
        # Tab 3: Account Management
        accounts_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(accounts_tab, text="👥 Tài khoản")
        self._create_accounts_tab(accounts_tab)
        
        # Tab 4: Auto Shutdown
        shutdown_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(shutdown_tab, text="⏰ Hẹn giờ")
        self._create_shutdown_tab(shutdown_tab)
        
        # Right side: Log area
        self._create_log_section(middle_frame)
    
    def _create_control_section(self, parent):
        """Tạo section điều khiển chính"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side: Status
        left_frame = ttk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(left_frame, text="⏸️ Đang dừng", 
                                      font=('Arial', 12, 'bold'), foreground='#666')
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.jobs_count_label = ttk.Label(left_frame, text="Jobs: 0", 
                                          font=('Arial', 10), foreground='#888')
        self.jobs_count_label.pack(side=tk.LEFT, padx=15)
        
        # Right side: Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(btn_frame, text="▶️ Bắt đầu", 
                                    style='Start.TButton', command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Dừng", 
                                   style='Stop.TButton', command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút Restart LDPlayer
        self.restart_ld_btn = ttk.Button(btn_frame, text="🔄 Restart LD", 
                                         command=self._restart_ldplayer, width=12)
        self.restart_ld_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(btn_frame, text="💾 Lưu cấu hình", 
                                   style='Save.TButton', command=self.save_now)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Coin stats section (tắt để tối ưu performance)
        # self._create_coin_stats_section(parent)
    
    def _create_coin_stats_section(self, parent):
        """Tạo section thống kê xu"""
        stats_frame = ttk.LabelFrame(parent, text="💰 Thống kê xu", padding="10")
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Session stats
        session_frame = ttk.Frame(stats_frame)
        session_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(session_frame, text="Phiên này:", 
                 font=('Arial', 9, 'bold')).pack(anchor='w')
        self.session_coins_label = ttk.Label(session_frame, text="0 xu (0 jobs)", 
                                            font=('Arial', 11, 'bold'), foreground='#4CAF50')
        self.session_coins_label.pack(anchor='w')
        
        # Today stats
        today_frame = ttk.Frame(stats_frame)
        today_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(today_frame, text="Hôm nay:", 
                 font=('Arial', 9, 'bold')).pack(anchor='w')
        self.today_coins_label = ttk.Label(today_frame, text="0 xu (0 jobs)", 
                                          font=('Arial', 11), foreground='#2196F3')
        self.today_coins_label.pack(anchor='w')
        
        # Week stats
        week_frame = ttk.Frame(stats_frame)
        week_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(week_frame, text="7 ngày:", 
                 font=('Arial', 9, 'bold')).pack(anchor='w')
        self.week_coins_label = ttk.Label(week_frame, text="0 xu (0 jobs)", 
                                         font=('Arial', 11), foreground='#FF9800')
        self.week_coins_label.pack(anchor='w')
        
        # Month stats
        month_frame = ttk.Frame(stats_frame)
        month_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(month_frame, text="30 ngày:", 
                 font=('Arial', 9, 'bold')).pack(anchor='w')
        self.month_coins_label = ttk.Label(month_frame, text="0 xu (0 jobs)", 
                                          font=('Arial', 11), foreground='#9C27B0')
        self.month_coins_label.pack(anchor='w')
        
        # Refresh button
        refresh_btn = ttk.Button(stats_frame, text="🔄", width=3,
                                command=self.refresh_coin_stats)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Load initial stats
        self.refresh_coin_stats()
    
    def _create_templates_tab(self, parent):
        """Tạo tab Templates với sub-tabs"""
        # Tạo sub-notebook
        sub_notebook = ttk.Notebook(parent)
        sub_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Sub-tab 1: Job Icons
        job_tab = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(job_tab, text="🎯 Job Icons")
        self._create_template_list(job_tab, [
            ("Icon nhận job (tổng quát)", "job_icon"),
            ("Icon tim ❤️", "job_heart"),
            ("Icon like 👍", "job_like"),
            ("Icon comment 💬", "job_cmt"),
            ("Icon share 🔄", "job_share"),
            ("Icon follow ➕", "job_follow"),
        ])
        
        # Sub-tab 2: Status & Result
        status_tab = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(status_tab, text="✅ Status")
        self._create_template_list(status_tab, [
            ("Icon hoàn thành ✓", "complete_icon"),
            ("Icon thất bại ✗", "fail_icon"),
            ("Nút báo lỗi", "fail_button"),
            ("Nút OK", "ok_button"),
            ("Nút Confirm", "confirm_button"),
            ("Nút Copy", "copy_button"),
        ])
        
        # Sub-tab 3: Navigation
        nav_tab = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(nav_tab, text="🧭 Navigation")
        self._create_template_list(nav_tab, [
            ("Icon Facebook", "fb_icon"),
            ("Icon Golike (LDPlayer)", "golike_icon"),
            ("Nút Home", "home_button"),
            ("Nút Danh mục", "category_button"),
            ("Nút Kiếm tiền", "earn_button"),
            ("Header 'Kiếm thưởng'", "earn_page_header"),
        ])
        
        # Sub-tab 4: Account Switching
        account_tab = ttk.Frame(sub_notebook, padding="10")
        sub_notebook.add(account_tab, text="👤 Account")
        self._create_template_list(account_tab, [
            ("Popup 'Đã làm tối đa job'", "max_job_popup"),
            ("Popup 'Tài khoản bị block'", "blocked_account_popup"),
            ("Popup 'Lỗi' (chung)", "error_popup"),
            ("Nút 'Chọn tài khoản'", "account_selector"),
            ("Tài khoản hiện tại (đỏ)", "current_account_red"),
            ("Template tài khoản (avatar+tên)", "account_item"),
        ])
    
    def _create_template_list(self, parent, templates):
        """Tạo danh sách templates trong một tab"""
        # Info frame
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Hướng dẫn", padding="10")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Click nút 📤 để upload template tương ứng", 
                 font=('Arial', 9, 'italic')).pack(anchor='w')
        
        # Templates frame
        templates_frame = ttk.Frame(parent)
        templates_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for idx, (label, key) in enumerate(templates):
            row_frame = ttk.Frame(templates_frame)
            row_frame.pack(fill=tk.X, pady=3)
            
            # Button
            btn = ttk.Button(row_frame, text=f"📤 {label}", 
                           command=lambda k=key: self.load_template(k),
                           width=40)
            btn.pack(side=tk.LEFT, padx=5)
            
            # Status indicator
            status = ttk.Label(row_frame, text="", width=3, font=('Arial', 12))
            status.pack(side=tk.LEFT, padx=5)
            
            # Store reference
            if not hasattr(self, 'template_status_labels'):
                self.template_status_labels = {}
            self.template_status_labels[key] = status
    

    
    def _create_settings_tab(self, parent):
        """Tạo tab Settings"""
        # Scrollable frame
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ADB Mode Group
        adb_frame = ttk.LabelFrame(scrollable_frame, text="🎮 Chế độ LDPlayer (ADB)", padding="15")
        adb_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_adb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adb_frame, text="✅ Sử dụng ADB (chỉ quét trong LDPlayer, không chiếm chuột)", 
                       variable=self.use_adb_var,
                       command=self._on_adb_toggle).pack(anchor='w', pady=5)
        
        ttk.Label(adb_frame, text="Đường dẫn ADB:", 
                 font=('Arial', 9)).pack(anchor='w', pady=(5, 2))
        adb_path_frame = ttk.Frame(adb_frame)
        adb_path_frame.pack(fill=tk.X, pady=3)
        self.adb_path_entry = ttk.Entry(adb_path_frame, width=40)
        self.adb_path_entry.insert(0, "adb")
        self.adb_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(adb_path_frame, text="📁", width=3,
                  command=self._browse_adb).pack(side=tk.LEFT)
        
        ttk.Label(adb_frame, text="Port LDPlayer:", 
                 font=('Arial', 9)).pack(anchor='w', pady=(5, 2))
        self.adb_port_entry = ttk.Entry(adb_frame, width=10)
        self.adb_port_entry.insert(0, "5555")
        self.adb_port_entry.pack(anchor='w', pady=3)
        
        # Golike Package Name
        ttk.Label(adb_frame, text="Package Golike (để mở app):", 
                 font=('Arial', 9)).pack(anchor='w', pady=(5, 2))
        self.golike_package_entry = ttk.Entry(adb_frame, width=40)
        self.golike_package_entry.insert(0, "com.golike")
        self.golike_package_entry.pack(anchor='w', pady=3)
        ttk.Label(adb_frame, text="💡 Để tìm package: adb shell pm list packages | grep golike", 
                 font=('Arial', 8, 'italic'), foreground='#666').pack(anchor='w')
        
        # Device selector (cho trường hợp nhiều devices)
        ttk.Label(adb_frame, text="Chọn Device (nếu có nhiều):", 
                 font=('Arial', 9)).pack(anchor='w', pady=(5, 2))
        device_frame = ttk.Frame(adb_frame)
        device_frame.pack(fill=tk.X, pady=3)
        self.adb_device_combo = ttk.Combobox(device_frame, width=30, state='readonly')
        self.adb_device_combo.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(device_frame, text="🔄 Quét devices", width=15,
                  command=self._scan_adb_devices).pack(side=tk.LEFT)
        
        self.adb_status_label = ttk.Label(adb_frame, text="⚪ Chưa kết nối", 
                                         font=('Arial', 9, 'bold'), foreground='#888')
        self.adb_status_label.pack(anchor='w', pady=5)
        
        ttk.Button(adb_frame, text="🔌 Kết nối ADB", 
                  command=self._test_adb_connection).pack(anchor='w', pady=5)
        
        ttk.Label(adb_frame, text="💡 Lưu ý: Cần cài đặt ADB và bật ADB trong LDPlayer", 
                 font=('Arial', 8, 'italic'), foreground='#666').pack(anchor='w', pady=(5, 0))
        
        # Back Action Group
        back_frame = ttk.LabelFrame(scrollable_frame, text="🔙 Hành động BACK", padding="15")
        back_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.back_method_var = tk.StringVar(value='click')
        
        ttk.Radiobutton(back_frame, text="📍 Click tọa độ", 
                       variable=self.back_method_var, value='click').pack(anchor='w', pady=3)
        
        coord_frame = ttk.Frame(back_frame)
        coord_frame.pack(fill=tk.X, padx=20, pady=3)
        ttk.Label(coord_frame, text="Tọa độ (x,y):").pack(side=tk.LEFT)
        self.back_coord_entry = ttk.Entry(coord_frame, width=15)
        self.back_coord_entry.insert(0, "60,1040")
        self.back_coord_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(back_frame, text="⌨️ Nhấn phím (F2 hoặc Back button)", 
                       variable=self.back_method_var, value='key').pack(anchor='w', pady=3)
        
        ttk.Label(back_frame, text="   💡 ADB mode: Dùng Back button Android", 
                 font=('Arial', 8, 'italic'), foreground='#666').pack(anchor='w', padx=20)
        
        ttk.Radiobutton(back_frame, text="🎮 Chuyển về Golike (LDPlayer)", 
                       variable=self.back_method_var, value='focus_golike').pack(anchor='w', pady=3)
        
        # Confidence Settings
        conf_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Độ tin cậy (Confidence)", padding="15")
        conf_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(conf_frame, text="Nhập 6 giá trị cách nhau bởi dấu phẩy:", 
                 font=('Arial', 9, 'italic')).pack(anchor='w', pady=(0, 5))
        ttk.Label(conf_frame, text="Job, Facebook, Hoàn thành, Thất bại, Nút lỗi, Nút OK", 
                 foreground='#666').pack(anchor='w', pady=(0, 5))
        
        self.conf_entry = ttk.Entry(conf_frame, width=50, font=('Consolas', 10))
        self.conf_entry.insert(0, "0.85,0.85,0.90,0.90,0.85,0.85")
        self.conf_entry.pack(fill=tk.X, pady=5)
        
        # Timeout Settings
        timeout_frame = ttk.LabelFrame(scrollable_frame, text="⏱️ Thời gian chờ (Timeout)", padding="15")
        timeout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(timeout_frame, text="Nhập 4 giá trị (giây) cách nhau bởi dấu phẩy:", 
                 font=('Arial', 9, 'italic')).pack(anchor='w', pady=(0, 5))
        ttk.Label(timeout_frame, text="Job, Facebook, Hoàn thành, Thất bại", 
                 foreground='#666').pack(anchor='w', pady=(0, 5))
        
        self.timeout_entry = ttk.Entry(timeout_frame, width=50, font=('Consolas', 10))
        self.timeout_entry.insert(0, "8,8,6,6")
        self.timeout_entry.pack(fill=tk.X, pady=5)
        
        # Timing Settings
        timing_frame = ttk.LabelFrame(scrollable_frame, text="⏲️ Khoảng cách giữa các job", padding="15")
        timing_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(timing_frame, text="Thời gian chờ ngẫu nhiên giữa min và max (giây):", 
                 font=('Arial', 9, 'italic')).pack(anchor='w', pady=(0, 5))
        
        between_frame = ttk.Frame(timing_frame)
        between_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(between_frame, text="Min, Max:").pack(side=tk.LEFT)
        self.between_entry = ttk.Entry(between_frame, width=15, font=('Consolas', 10))
        self.between_entry.insert(0, "2.0,3.0")
        self.between_entry.pack(side=tk.LEFT, padx=5)
        
        # Other Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Tùy chọn khác", padding="15")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.close_tab_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="🗙 Đóng tab trình duyệt sau mỗi job (Ctrl+W)", 
                       variable=self.close_tab_var).pack(anchor='w', pady=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    

    
    def _create_log_section(self, parent):
        """Tạo log section"""
        log_frame = ttk.LabelFrame(parent, text="📝 Nhật ký hoạt động", padding="10")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(log_controls, text="🗑️ Xóa log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_controls, text="📜 Tự động cuộn", 
                       variable=self.auto_scroll_var).pack(side=tk.LEFT, padx=5)
        
        # Log text area
        self.log_box = scrolledtext.ScrolledText(log_frame, width=50,
                                                 font=('Consolas', 9),
                                                 wrap=tk.WORD,
                                                 background='#1e1e1e',
                                                 foreground='#d4d4d4')
        self.log_box.pack(fill=tk.BOTH, expand=True)
        
        # Configure log tags for colors
        self.log_box.tag_config('info', foreground='#4EC9B0')
        self.log_box.tag_config('success', foreground='#4CAF50')
        self.log_box.tag_config('warning', foreground='#FFA500')
        self.log_box.tag_config('error', foreground='#f44336')
    
    def clear_log(self):
        """Xóa log"""
        self.log_box.delete('1.0', tk.END)
    
    def append_log(self, s):
        """Thêm log message với color coding"""
        # Determine tag based on content
        tag = 'info'
        if '✓' in s or 'thành công' in s.lower() or 'hoàn thành' in s.lower():
            tag = 'success'
        elif '⚠' in s or 'warning' in s.lower() or 'cảnh báo' in s.lower():
            tag = 'warning'
        elif '✗' in s or 'lỗi' in s.lower() or 'thất bại' in s.lower() or 'fail' in s.lower():
            tag = 'error'
        
        self.log_box.insert(tk.END, s + "\n", tag)
        
        if self.auto_scroll_var.get():
            self.log_box.see(tk.END)
    
    def apply_settings_to_ui(self):
        """Áp dụng settings đã lưu vào UI"""
        if not self.settings:
            return
        
        # Load templates (chỉ đếm, không log từng cái)
        t = self.settings.get('templates', {})
        template_count = 0
        for k, p in t.items():
            if os.path.exists(p):
                self.templates[k] = p
                template_count += 1
                # Update status indicator
                if hasattr(self, 'template_status_labels') and k in self.template_status_labels:
                    self.template_status_labels[k].config(text="✓", foreground='#4CAF50')
        
        if template_count > 0:
            self.append_log(f"✓ Đã tải {template_count} templates")
        
        # Load other settings
        confs = self.settings.get('confs')
        if confs:
            self.conf_entry.delete(0, tk.END)
            self.conf_entry.insert(0, ",".join(str(x) for x in confs))
        
        timeouts = self.settings.get('timeouts')
        if timeouts:
            self.timeout_entry.delete(0, tk.END)
            self.timeout_entry.insert(0, ",".join(str(x) for x in timeouts))
        
        back_method = self.settings.get('back_method')
        if back_method:
            self.back_method_var.set(back_method)
        
        bc = self.settings.get('back_coord')
        if bc:
            self.back_coord_entry.delete(0, tk.END)
            self.back_coord_entry.insert(0, f"{bc[0]},{bc[1]}")
        
        between = self.settings.get('between')
        if between:
            self.between_entry.delete(0, tk.END)
            self.between_entry.insert(0, f"{between[0]},{between[1]}")
        
        self.close_tab_var.set(self.settings.get('close_tab_after', False))
        
        # Load ADB settings
        self.use_adb_var.set(self.settings.get('use_adb', False))
        adb_path = self.settings.get('adb_path', 'adb')
        if adb_path:
            self.adb_path_entry.delete(0, tk.END)
            self.adb_path_entry.insert(0, adb_path)
        adb_port = self.settings.get('adb_port', 5555)
        if adb_port:
            self.adb_port_entry.delete(0, tk.END)
            self.adb_port_entry.insert(0, str(adb_port))
        adb_device = self.settings.get('adb_device', '')
        if adb_device and hasattr(self, 'adb_device_combo'):
            self.adb_device_combo.set(adb_device)
        
        # Golike package
        golike_pkg = self.settings.get('golike_package', 'com.golike')
        if hasattr(self, 'golike_package_entry'):
            self.golike_package_entry.delete(0, tk.END)
            self.golike_package_entry.insert(0, golike_pkg)
        
        self.append_log("✅ Sẵn sàng!")
    
    def _lazy_init(self):
        """Khởi tạo các thành phần nặng sau khi GUI đã hiển thị"""
        try:
            # Import lazy
            from Controllers.sequence_worker import SequenceWorker
            
            # Init worker
            self.worker = SequenceWorker(self)
            
            # Apply settings
            self.apply_settings_to_ui()
        except Exception as e:
            self.append_log(f"⚠️ Lỗi khi khởi tạo: {e}")
    

    
    def load_template(self, key):
        """Load template image"""
        p = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.bmp")])
        if not p:
            return
        
        try:
            # Import lazy
            from Utils.image_utils import copy_template_to_store
            
            dst = copy_template_to_store(p, key)
            self.templates[key] = dst
            
            # Update status indicator
            if hasattr(self, 'template_status_labels') and key in self.template_status_labels:
                self.template_status_labels[key].config(text="✓", foreground='#4CAF50')
            
            self.append_log(f"✓ Đã tải template {key}: {os.path.basename(dst)}")
            self.settings = self.compose_settings()
            save_settings(self.settings)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu template: {e}")
            self.append_log(f"✗ Lỗi khi tải template {key}: {e}")
    
    def compose_settings(self):
        """Tạo settings dict từ UI"""
        confs = [float(x.strip()) for x in self.conf_entry.get().split(',') if x.strip()]
        while len(confs) < 6:
            confs.append(confs[-1] if confs else 0.85)
        
        timeouts = [float(x.strip()) for x in self.timeout_entry.get().split(',') if x.strip()]
        while len(timeouts) < 4:
            timeouts.append(timeouts[-1] if timeouts else 6.0)
        
        try:
            a, b = [float(x.strip()) for x in self.between_entry.get().split(',') if x.strip()]
        except Exception:
            a, b = 2.0, 3.0
        
        back = self.back_method_var.get()
        bc = None
        try:
            s = self.back_coord_entry.get().strip()
            parts = [int(x.strip()) for x in s.split(',') if x.strip()]
            if len(parts) >= 2:
                bc = (parts[0], parts[1])
        except Exception:
            bc = None
        
        st = {
            'templates': self.templates,
            'confs': confs,
            'timeouts': timeouts,
            'between': (a, b),
            'back_method': back,
            'back_coord': bc,
            'close_tab_after': bool(self.close_tab_var.get()),
            'jobs_file': self.settings.get('jobs_file') if self.settings else None,
            'use_adb': bool(self.use_adb_var.get()),
            'adb_path': self.adb_path_entry.get().strip(),
            'adb_port': int(self.adb_port_entry.get().strip()) if self.adb_port_entry.get().strip().isdigit() else 5555,
            'adb_device': self.adb_device_combo.get().strip() if hasattr(self, 'adb_device_combo') else ''
        }
        return st
    
    def save_now(self):
        """Lưu cấu hình ngay"""
        self.settings = self.compose_settings()
        ok = save_settings(self.settings)
        if ok:
            self.append_log("✓ Đã lưu cấu hình vào settings.json")
            messagebox.showinfo("Thành công", "Đã lưu cấu hình!")
        else:
            self.append_log("✗ Lưu cấu hình thất bại")
            messagebox.showerror("Lỗi", "Không thể lưu cấu hình!")
    
    def parse_params(self):
        """Parse parameters từ UI"""
        confs = [float(x.strip()) for x in self.conf_entry.get().split(',') if x.strip()]
        while len(confs) < 6:
            confs.append(confs[-1] if confs else 0.85)
        
        timeouts = [float(x.strip()) for x in self.timeout_entry.get().split(',') if x.strip()]
        while len(timeouts) < 4:
            timeouts.append(timeouts[-1] if timeouts else 6.0)
        
        try:
            mins, maxs = [float(x.strip()) for x in self.between_entry.get().split(',') if x.strip()]
        except Exception:
            mins, maxs = 2.0, 3.0
        
        back = self.back_method_var.get()
        try:
            s = self.back_coord_entry.get().strip()
            parts = [int(x.strip()) for x in s.split(',') if x.strip()]
            bc = (parts[0], parts[1]) if len(parts) >= 2 else None
        except Exception:
            bc = None
        
        # Golike package
        golike_pkg = self.golike_package_entry.get().strip() or 'com.golike.app'
        
        params = {
            'conf_job': confs[0],
            'conf_fb': confs[1],
            'conf_complete': confs[2],
            'conf_fail': confs[3],
            'conf_failbtn': confs[4],
            'conf_okbtn': confs[5],
            'conf_golike': confs[0],
            'conf_golike_fallback': 0.80,
            'timeout_job': timeouts[0],
            'timeout_fb': timeouts[1],
            'timeout_complete': timeouts[2],
            'timeout_fail': timeouts[3],
            'back_method': back,
            'back_coord': bc,
            'min_between': mins,
            'max_between': maxs,
            'click_complete': True,
            'close_tab_after': bool(self.close_tab_var.get()),
            'golike_package': golike_pkg
        }
        
        self.settings = self.compose_settings()
        save_settings(self.settings)
        return params
    
    def start(self):
        """Bắt đầu worker"""
        if not self.worker:
            self.append_log("⚠️ Worker chưa sẵn sàng, vui lòng đợi...")
            return
        
        params = self.parse_params()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="▶️ Đang chạy", foreground='#4CAF50')
        
        # Reset session coins (lazy import)
        try:
            from Models.coin_tracker import get_coin_tracker
            tracker = get_coin_tracker()
            tracker.reset_session()
            self.refresh_coin_stats()
        except Exception:
            pass
        
        self.append_log("=" * 60)
        self.append_log("▶️ BẮT ĐẦU WORKER")
        self.append_log("=" * 60)
        self.worker.start(self.jobs, self.templates, params)
    
    def stop(self):
        """Dừng worker"""
        if not self.worker:
            return
        
        self.append_log("⏹️ Yêu cầu dừng...")
        self.worker.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏸️ Đã dừng", foreground='#666')
        self.append_log("=" * 60)
        self.append_log("⏹️ ĐÃ DỪNG WORKER")
        self.append_log("=" * 60)
    
    def _restart_ldplayer(self):
        """Restart LDPlayer"""
        from Utils.ldplayer_manager import LDPlayerManager
        import threading
        import tkinter.messagebox as msgbox
        
        # Confirm
        confirm = msgbox.askyesno(
            "Restart LDPlayer",
            "Bạn có chắc muốn restart LDPlayer?\n\n"
            "Bot sẽ tự động dừng và LDPlayer sẽ khởi động lại.\n"
            "Quá trình này mất khoảng 30-40 giây."
        )
        
        if not confirm:
            return
        
        # Dừng bot nếu đang chạy
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            self.stop()
            time.sleep(2)
        
        self.append_log("🔄 Đang restart LDPlayer...")
        self.restart_ld_btn.config(state=tk.DISABLED)
        
        def restart_thread():
            try:
                manager = LDPlayerManager()
                success = manager.restart_ldplayer(index=0)
                
                if success:
                    self.append_log("✅ LDPlayer đã restart thành công!")
                    
                    # Đợi lâu hơn để LDPlayer khởi động hoàn toàn
                    self.append_log("⏳ Đợi LDPlayer khởi động hoàn toàn (20 giây)...")
                    time.sleep(20)
                    
                    # Mở app Golike nếu đang dùng ADB mode
                    use_adb = self.use_adb_var.get() if hasattr(self, 'use_adb_var') else False
                    if use_adb:
                        self.append_log("📱 Đang mở app Golike...")
                        app_opened = self._open_golike_after_restart()
                        
                        if app_opened:
                            # Đợi app load hoàn toàn
                            self.append_log("⏳ Đợi app Golike load (10 giây)...")
                            time.sleep(10)
                            
                            # Reset navigation để vào màn hình "Kiếm thưởng"
                            self.append_log("🧭 Đang vào màn hình 'Kiếm thưởng'...")
                            nav_success = self._reset_navigation_after_restart()
                            
                            if nav_success:
                                self.append_log("✅ Đã vào màn hình 'Kiếm thưởng'!")
                                
                                # Tự động chạy bot
                                self.append_log("▶️ Tự động bắt đầu bot...")
                                time.sleep(2)
                                self.master.after(100, self.start)  # Gọi start() từ main thread
                            else:
                                self.append_log("⚠️ Chưa vào được màn hình 'Kiếm thưởng'")
                                self.append_log("💡 Vui lòng vào thủ công và bắt đầu bot")
                        else:
                            self.append_log("⚠️ Không mở được app Golike")
                            self.append_log("💡 Vui lòng mở thủ công và bắt đầu bot")
                    else:
                        self.append_log("💡 Bạn có thể bắt đầu bot lại")
                else:
                    self.append_log("⚠️ Restart LDPlayer không thành công")
                    self.append_log("💡 Vui lòng restart thủ công")
            except Exception as e:
                self.append_log(f"❌ Lỗi: {e}")
                import traceback
                self.append_log(f"Traceback: {traceback.format_exc()}")
            finally:
                self.restart_ld_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=restart_thread, daemon=True).start()
    
    def _open_golike_after_restart(self):
        """
        Mở app Golike sau khi restart LDPlayer
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            from Utils.adb_utils import ADBController
            
            # Kết nối lại ADB (sau restart phải kết nối lại)
            adb_path = self.adb_path_entry.get().strip() if hasattr(self, 'adb_path_entry') else "adb"
            adb_port = int(self.adb_port_entry.get().strip()) if hasattr(self, 'adb_port_entry') and self.adb_port_entry.get().strip().isdigit() else 5555
            
            self.append_log(f"   🔌 Kết nối lại ADB...")
            
            # Thử kết nối nhiều lần
            controller = ADBController(adb_path=adb_path)
            max_retries = 5
            
            for attempt in range(max_retries):
                if controller.connect(port=adb_port):
                    self.append_log(f"   ✓ Đã kết nối ADB - Device: {controller.device_id}")
                    
                    # Cập nhật controller cho window_utils và image_utils
                    from Utils.window_utils import set_adb_mode as window_set_adb_mode
                    from Utils.image_utils import set_adb_mode as image_set_adb_mode
                    window_set_adb_mode(True, controller)
                    image_set_adb_mode(True, controller)
                    
                    break
                else:
                    if attempt < max_retries - 1:
                        self.append_log(f"   ⏳ Thử lại kết nối ADB ({attempt + 1}/{max_retries})...")
                        time.sleep(5)
                    else:
                        self.append_log(f"   ⚠️ Không thể kết nối ADB sau {max_retries} lần thử")
                        return False
            
            # Đợi thêm để LDPlayer ổn định hoàn toàn
            self.append_log(f"   ⏳ Đợi LDPlayer ổn định (5 giây)...")
            time.sleep(5)
            
            # Nhấn Home để về màn hình chính (đảm bảo không có app nào đang chạy)
            self.append_log(f"   🏠 Nhấn Home button để về màn hình chính...")
            controller.press_home()
            time.sleep(3)
            
            # Cách 1: Thử mở app bằng package name
            golike_package = self.golike_package_entry.get().strip() if hasattr(self, 'golike_package_entry') else 'com.golike.app'
            self.append_log(f"   📱 Mở app Golike ({golike_package})...")
            success = controller.open_app(golike_package)
            
            if success:
                self.append_log(f"   ✓ Đã gửi lệnh mở app")
                
                # Đợi app load
                self.append_log(f"   ⏳ Đợi app load (8 giây)...")
                time.sleep(8)
                
                # Nhấn Space để tắt popup (nếu có)
                self.append_log(f"   ⏎ Nhấn Space để tắt popup...")
                controller.press_key("KEYCODE_SPACE")
                time.sleep(1)
                
                return True
            else:
                # Cách 2: Tìm icon Golike trên Home
                self.append_log(f"   ⚠️ Không mở được bằng package name")
                self.append_log(f"   🔍 Tìm icon Golike trên màn hình Home...")
                
                if self._click_golike_icon():
                    self.append_log(f"   ✓ Đã click icon Golike")
                    
                    # Đợi app load
                    time.sleep(8)
                    
                    # Nhấn Space để tắt popup
                    self.append_log(f"   ⏎ Nhấn Space để tắt popup...")
                    controller.press_key("KEYCODE_SPACE")
                    time.sleep(1)
                    
                    return True
                else:
                    self.append_log(f"   ⚠️ Không tìm thấy icon Golike")
                    return False
                
        except Exception as e:
            self.append_log(f"   ⚠️ Lỗi khi mở app: {e}")
            import traceback
            self.append_log(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def _click_understood_button(self):
        """Click nút 'Đã hiểu' để tắt popup thông báo khi mới vào app"""
        try:
            from Utils.image_utils import load_gray, locate_template
            from Utils.window_utils import click_at
            
            self.append_log("   🔍 Tìm nút 'Đã hiểu'...")
            
            # Tìm template "understood_button" hoặc "da_hieu"
            understood_keys = ['understood_button', 'da_hieu_button', 'ok_popup']
            
            for key in understood_keys:
                if key in self.templates:
                    template_path = self.templates[key]
                    try:
                        tmpl = load_gray(template_path)
                        found = locate_template(tmpl, confidence=0.80, timeout=3.0, step=0.1, region=None)
                        
                        if found:
                            x, y, score = found
                            self.append_log(f"   ✓ Tìm thấy nút 'Đã hiểu' tại ({x}, {y})")
                            click_at(x, y)
                            time.sleep(0.5)
                            self.append_log(f"   ✓ Đã click nút 'Đã hiểu'")
                            return
                    except Exception as e:
                        self.append_log(f"   ⚠️ Lỗi khi tìm '{key}': {e}")
            
            self.append_log(f"   ⚠️ Không tìm thấy nút 'Đã hiểu' - Có thể không có popup")
            self.append_log(f"   💡 Tip: Upload template 'understood_button' nếu có popup")
            
        except Exception as e:
            self.append_log(f"   ⚠️ Lỗi khi click nút 'Đã hiểu': {e}")
    
    def _click_golike_icon(self):
        """
        Tìm và click icon Golike trên màn hình Home
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            from Utils.image_utils import load_gray, locate_template_multiscale
            from Utils.window_utils import click_at
            
            # Tìm template golike_icon
            golike_keys = ['golike_icon', 'ld_golike_icon', 'golike']
            
            for key in golike_keys:
                if key in self.templates:
                    template_path = self.templates[key]
                    try:
                        tmpl = load_gray(template_path)
                        
                        # Tìm với confidence thấp hơn
                        found = locate_template_multiscale(
                            tmpl, confidence=0.75, timeout=5.0,
                            step=0.08, region=None
                        )
                        
                        if found:
                            x, y, score = found
                            self.append_log(f"      ✓ Tìm thấy icon '{key}' tại ({x}, {y}) score={score:.2f}")
                            click_at(x, y)
                            time.sleep(0.5)
                            return True
                    except Exception as e:
                        self.append_log(f"      ⚠️ Lỗi khi tìm '{key}': {e}")
            
            return False
            
        except Exception as e:
            self.append_log(f"      ⚠️ Lỗi khi click icon Golike: {e}")
            return False
    
    def _reset_navigation_after_restart(self):
        """
        Reset navigation sau khi restart để vào màn hình 'Kiếm thưởng'
        Returns: True nếu thành công, False nếu thất bại
        """
        try:
            from Controllers.reset_navigation import ResetNavigation
            
            # Lấy templates và params
            templates = self.templates
            params = self.parse_params()
            
            # Tạo should_stop function (luôn return False vì không cần dừng)
            def should_stop():
                return False
            
            # Tạo reset navigation instance
            resetter = ResetNavigation(templates, params, log_fn=self.append_log, should_stop_fn=should_stop)
            
            # Chạy reset (method đúng là perform_reset)
            resetter.perform_reset()
            
            self.append_log("   ✓ Reset navigation hoàn tất")
            return True
            
        except Exception as e:
            self.append_log(f"   ⚠️ Lỗi khi reset navigation: {e}")
            import traceback
            self.append_log(f"   Traceback: {traceback.format_exc()}")
            return False

    def _browse_adb(self):
        """Chọn file adb.exe"""
        p = filedialog.askopenfilename(
            title="Chọn adb.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if p:
            self.adb_path_entry.delete(0, tk.END)
            self.adb_path_entry.insert(0, p)
    
    def _on_adb_toggle(self):
        """Xử lý khi toggle ADB mode"""
        if self.use_adb_var.get():
            self.append_log("ℹ️ Đã bật chế độ ADB - Nhớ kết nối ADB trước khi chạy!")
        else:
            self.append_log("ℹ️ Đã tắt chế độ ADB - Sử dụng chế độ toàn màn hình")
    
    def _scan_adb_devices(self):
        """Quét và hiển thị danh sách ADB devices"""
        from Utils.adb_utils import ADBController
        
        adb_path = self.adb_path_entry.get().strip() or "adb"
        self.append_log("🔍 Đang quét ADB devices...")
        
        controller = ADBController(adb_path=adb_path)
        devices = controller.get_devices()
        
        if devices:
            self.adb_device_combo['values'] = devices
            if len(devices) == 1:
                self.adb_device_combo.current(0)
            self.append_log(f"✓ Tìm thấy {len(devices)} device(s): {devices}")
            messagebox.showinfo("Thành công", f"Tìm thấy {len(devices)} device(s):\n" + "\n".join(devices))
        else:
            self.adb_device_combo['values'] = []
            self.append_log("⚠ Không tìm thấy device nào")
            messagebox.showwarning("Cảnh báo", 
                "Không tìm thấy device nào!\n\n"
                "Kiểm tra:\n"
                "1. LDPlayer đã chạy chưa\n"
                "2. ADB Debug đã bật chưa\n"
                "3. Thử: adb kill-server → adb start-server")
    
    def _test_adb_connection(self):
        """Test kết nối ADB"""
        from Utils.adb_utils import ADBController
        
        adb_path = self.adb_path_entry.get().strip() or "adb"
        try:
            port = int(self.adb_port_entry.get().strip())
        except Exception:
            port = 5555
        
        # Lấy device_id nếu đã chọn
        selected_device = self.adb_device_combo.get().strip()
        
        self.append_log(f"🔌 Đang kết nối ADB...")
        
        controller = ADBController(adb_path=adb_path)
        
        # Nếu có chọn device cụ thể, dùng luôn
        if selected_device:
            if controller.connect(port=port, device_id=selected_device):
                self.adb_status_label.config(text="🟢 Đã kết nối", foreground='#4CAF50')
                self.append_log(f"✓ Kết nối ADB thành công! Device: {selected_device}")
                
                # Test screenshot
                screen_size = controller.get_screen_size()
                if screen_size:
                    self.append_log(f"✓ Kích thước màn hình: {screen_size[0]}x{screen_size[1]}")
                
                messagebox.showinfo("Thành công", f"Kết nối ADB thành công!\nDevice: {selected_device}")
                return
        
        # Không có device được chọn, thử auto-connect
        if controller.connect(port=port):
            devices = controller.get_devices()
            self.adb_status_label.config(text="🟢 Đã kết nối", foreground='#4CAF50')
            self.append_log(f"✓ Kết nối ADB thành công! Device: {controller.device_id}")
            
            # Cập nhật combo box
            if devices:
                self.adb_device_combo['values'] = devices
                if controller.device_id in devices:
                    self.adb_device_combo.set(controller.device_id)
            
            # Test screenshot
            screen_size = controller.get_screen_size()
            if screen_size:
                self.append_log(f"✓ Kích thước màn hình: {screen_size[0]}x{screen_size[1]}")
            
            messagebox.showinfo("Thành công", f"Kết nối ADB thành công!\nDevice: {controller.device_id}")
        else:
            self.adb_status_label.config(text="🔴 Kết nối thất bại", foreground='#f44336')
            
            # Kiểm tra xem có nhiều devices không
            devices = controller.get_devices()
            if len(devices) > 1:
                self.append_log(f"⚠ Có {len(devices)} devices. Vui lòng chọn device cụ thể!")
                self.adb_device_combo['values'] = devices
                messagebox.showerror("Lỗi", 
                    f"Có {len(devices)} devices đang kết nối!\n\n"
                    f"Devices: {', '.join(devices)}\n\n"
                    "Vui lòng:\n"
                    "1. Click '🔄 Quét devices'\n"
                    "2. Chọn device từ dropdown\n"
                    "3. Click '🔌 Kết nối ADB' lại")
            else:
                self.append_log("✗ Kết nối ADB thất bại!")
                messagebox.showerror("Lỗi", 
                    "Không thể kết nối ADB!\n\n"
                    "Kiểm tra:\n"
                    "1. ADB đã được cài đặt\n"
                    "2. LDPlayer đã bật ADB Debug\n"
                    "3. Port đúng (mặc định 5555)\n"
                    "4. Thử: adb kill-server → adb start-server")

    def refresh_coin_stats(self):
        """Cập nhật hiển thị thống kê xu (tắt để tối ưu)"""
        pass
        # from coin_tracker import get_coin_tracker
        # tracker = get_coin_tracker()
        # session = tracker.get_session_stats()
        # self.session_coins_label.config(text=f"{session['coins']} xu ({session['jobs']} jobs)")
        # ...
    
    def add_coins(self, coins):
        """Thêm xu và cập nhật UI (tắt để tối ưu)"""
        pass
        # from coin_tracker import get_coin_tracker
        # tracker = get_coin_tracker()
        # tracker.add_coins(coins)
        # self.refresh_coin_stats()
        # self.append_log(f"💰 +{coins} xu | Tổng phiên: {tracker.session_coins} xu")

    def _create_accounts_tab(self, parent):
        """Tạo tab quản lý tài khoản (blocked và max job)"""
        # Title
        title_label = ttk.Label(parent, text="Quản lý tài khoản", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Blocked accounts section
        blocked_frame = ttk.LabelFrame(parent, text="🔒 Tài khoản bị blocked (vĩnh viễn)", padding="10")
        blocked_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox + Scrollbar
        blocked_list_frame = ttk.Frame(blocked_frame)
        blocked_list_frame.pack(fill=tk.BOTH, expand=True)
        
        blocked_scrollbar = ttk.Scrollbar(blocked_list_frame)
        blocked_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.blocked_listbox = tk.Listbox(blocked_list_frame, 
                                          yscrollcommand=blocked_scrollbar.set,
                                          font=('Consolas', 10),
                                          selectmode=tk.SINGLE)
        self.blocked_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        blocked_scrollbar.config(command=self.blocked_listbox.yview)
        
        # Buttons
        blocked_btn_frame = ttk.Frame(blocked_frame)
        blocked_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(blocked_btn_frame, text="🔄 Làm mới", 
                  command=self._refresh_blocked_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(blocked_btn_frame, text="❌ Xóa đã chọn", 
                  command=self._remove_blocked_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(blocked_btn_frame, text="🗑️ Xóa tất cả", 
                  command=self._clear_all_blocked).pack(side=tk.LEFT)
        
        # Max job accounts section
        maxjob_frame = ttk.LabelFrame(parent, text="🚫 Tài khoản max job (reset mỗi ngày)", padding="10")
        maxjob_frame.pack(fill=tk.BOTH, expand=True)
        
        # Listbox + Scrollbar
        maxjob_list_frame = ttk.Frame(maxjob_frame)
        maxjob_list_frame.pack(fill=tk.BOTH, expand=True)
        
        maxjob_scrollbar = ttk.Scrollbar(maxjob_list_frame)
        maxjob_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.maxjob_listbox = tk.Listbox(maxjob_list_frame,
                                         yscrollcommand=maxjob_scrollbar.set,
                                         font=('Consolas', 10),
                                         selectmode=tk.SINGLE)
        self.maxjob_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        maxjob_scrollbar.config(command=self.maxjob_listbox.yview)
        
        # Buttons
        maxjob_btn_frame = ttk.Frame(maxjob_frame)
        maxjob_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(maxjob_btn_frame, text="🔄 Làm mới",
                  command=self._refresh_maxjob_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(maxjob_btn_frame, text="❌ Xóa đã chọn",
                  command=self._remove_maxjob_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(maxjob_btn_frame, text="🗑️ Xóa tất cả",
                  command=self._clear_all_maxjob).pack(side=tk.LEFT)
        
        # Load initial data
        self._refresh_blocked_list()
        self._refresh_maxjob_list()
    
    def _refresh_blocked_list(self):
        """Làm mới danh sách blocked accounts"""
        self.blocked_listbox.delete(0, tk.END)
        try:
            if os.path.exists('Models/blocked_accounts.txt'):
                with open('Models/blocked_accounts.txt', 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                    for acc in accounts:
                        self.blocked_listbox.insert(tk.END, acc)
                # Only log if log_box exists
                if hasattr(self, 'log_box'):
                    self.append_log(f"✓ Đã tải {len(accounts)} tài khoản blocked")
        except Exception as e:
            if hasattr(self, 'log_box'):
                self.append_log(f"⚠️ Lỗi khi tải blocked accounts: {e}")
    
    def _refresh_maxjob_list(self):
        """Làm mới danh sách max job accounts"""
        self.maxjob_listbox.delete(0, tk.END)
        try:
            if os.path.exists('Models/max_job_accounts.txt'):
                with open('Models/max_job_accounts.txt', 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                    for acc in accounts:
                        self.maxjob_listbox.insert(tk.END, acc)
                # Only log if log_box exists
                if hasattr(self, 'log_box'):
                    self.append_log(f"✓ Đã tải {len(accounts)} tài khoản max job")
        except Exception as e:
            if hasattr(self, 'log_box'):
                self.append_log(f"⚠️ Lỗi khi tải max job accounts: {e}")
    
    def _remove_blocked_account(self):
        """Xóa tài khoản blocked đã chọn"""
        selection = self.blocked_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản cần xóa")
            return
        
        account_id = self.blocked_listbox.get(selection[0])
        
        if messagebox.askyesno("Xác nhận", f"Xóa tài khoản {account_id} khỏi danh sách blocked?"):
            try:
                # Đọc file
                with open('Models/blocked_accounts.txt', 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                
                # Xóa tài khoản
                accounts = [acc for acc in accounts if acc != account_id]
                
                # Ghi lại file
                with open('Models/blocked_accounts.txt', 'w', encoding='utf-8') as f:
                    for acc in accounts:
                        f.write(f"{acc}\n")
                
                self.append_log(f"✓ Đã xóa {account_id} khỏi danh sách blocked")
                self._refresh_blocked_list()
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
    
    def _remove_maxjob_account(self):
        """Xóa tài khoản max job đã chọn"""
        selection = self.maxjob_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản cần xóa")
            return
        
        account_id = self.maxjob_listbox.get(selection[0])
        
        if messagebox.askyesno("Xác nhận", f"Xóa tài khoản {account_id} khỏi danh sách max job?"):
            try:
                # Đọc file
                with open('Models/max_job_accounts.txt', 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f if line.strip()]
                
                # Xóa tài khoản
                accounts = [acc for acc in accounts if acc != account_id]
                
                # Ghi lại file
                with open('Models/max_job_accounts.txt', 'w', encoding='utf-8') as f:
                    for acc in accounts:
                        f.write(f"{acc}\n")
                
                self.append_log(f"✓ Đã xóa {account_id} khỏi danh sách max job")
                self._refresh_maxjob_list()
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
    
    def _clear_all_blocked(self):
        """Xóa tất cả tài khoản blocked"""
        if messagebox.askyesno("Xác nhận", "Xóa TẤT CẢ tài khoản blocked?"):
            try:
                with open('Models/blocked_accounts.txt', 'w', encoding='utf-8') as f:
                    f.write('')
                self.append_log("✓ Đã xóa tất cả tài khoản blocked")
                self._refresh_blocked_list()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
    
    def _clear_all_maxjob(self):
        """Xóa tất cả tài khoản max job"""
        if messagebox.askyesno("Xác nhận", "Xóa TẤT CẢ tài khoản max job?"):
            try:
                with open('Models/max_job_accounts.txt', 'w', encoding='utf-8') as f:
                    f.write('')
                self.append_log("✓ Đã xóa tất cả tài khoản max job")
                self._refresh_maxjob_list()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")
    
    def _create_shutdown_tab(self, parent):
        """Tạo tab hẹn giờ tắt máy"""
        # Title
        title_label = ttk.Label(parent, text="Hẹn giờ tắt máy", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Description
        desc_label = ttk.Label(parent, 
                              text="Tool sẽ tự động tắt máy sau khoảng thời gian đã đặt",
                              style='Subtitle.TLabel')
        desc_label.pack(anchor='w', pady=(0, 20))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(parent, text="⏰ Cài đặt", padding="20")
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Enable checkbox
        self.shutdown_enabled_var = tk.BooleanVar(value=False)
        enable_check = ttk.Checkbutton(settings_frame, 
                                       text="Bật hẹn giờ tắt máy",
                                       variable=self.shutdown_enabled_var,
                                       command=self._toggle_shutdown)
        enable_check.pack(anchor='w', pady=(0, 15))
        
        # Time input
        time_frame = ttk.Frame(settings_frame)
        time_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(time_frame, text="Thời gian:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.shutdown_hours_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=23, width=5, 
                   textvariable=self.shutdown_hours_var).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(time_frame, text="giờ").pack(side=tk.LEFT, padx=(0, 15))
        
        self.shutdown_minutes_var = tk.StringVar(value="30")
        ttk.Spinbox(time_frame, from_=0, to=59, width=5,
                   textvariable=self.shutdown_minutes_var).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(time_frame, text="phút").pack(side=tk.LEFT)
        
        # Status frame
        status_frame = ttk.LabelFrame(parent, text="📊 Trạng thái", padding="20")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.shutdown_status_label = ttk.Label(status_frame, 
                                               text="⏸️ Chưa kích hoạt",
                                               font=('Arial', 11))
        self.shutdown_status_label.pack(pady=10)
        
        self.shutdown_countdown_label = ttk.Label(status_frame,
                                                  text="",
                                                  font=('Arial', 14, 'bold'),
                                                  foreground='#2196F3')
        self.shutdown_countdown_label.pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="▶️ Bắt đầu đếm ngược",
                  command=self._start_shutdown_timer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹️ Hủy",
                  command=self._cancel_shutdown_timer).pack(side=tk.LEFT, padx=5)
        
        # Timer variables
        self.shutdown_timer_active = False
        self.shutdown_end_time = None
    
    def _toggle_shutdown(self):
        """Toggle hẹn giờ tắt máy"""
        if self.shutdown_enabled_var.get():
            self.append_log("✓ Đã bật hẹn giờ tắt máy")
        else:
            self.append_log("✓ Đã tắt hẹn giờ tắt máy")
            self._cancel_shutdown_timer()
    
    def _start_shutdown_timer(self):
        """Bắt đầu đếm ngược tắt máy"""
        if not self.shutdown_enabled_var.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng bật hẹn giờ tắt máy trước")
            return
        
        try:
            hours = int(self.shutdown_hours_var.get())
            minutes = int(self.shutdown_minutes_var.get())
            
            if hours == 0 and minutes == 0:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập thời gian > 0")
                return
            
            total_seconds = hours * 3600 + minutes * 60
            self.shutdown_end_time = time.time() + total_seconds
            self.shutdown_timer_active = True
            
            self.append_log(f"⏰ Bắt đầu đếm ngược: {hours}h {minutes}m")
            self.shutdown_status_label.config(text="▶️ Đang đếm ngược...")
            
            # Start countdown
            self._update_shutdown_countdown()
            
        except ValueError:
            messagebox.showerror("Lỗi", "Thời gian không hợp lệ")
    
    def _update_shutdown_countdown(self):
        """Cập nhật đếm ngược"""
        if not self.shutdown_timer_active or self.shutdown_end_time is None:
            return
        
        remaining = self.shutdown_end_time - time.time()
        
        if remaining <= 0:
            # Time's up - shutdown
            self._execute_shutdown()
            return
        
        # Update display
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        self.shutdown_countdown_label.config(
            text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        )
        
        # Schedule next update
        self.master.after(1000, self._update_shutdown_countdown)
    
    def _cancel_shutdown_timer(self):
        """Hủy đếm ngược"""
        self.shutdown_timer_active = False
        self.shutdown_end_time = None
        self.shutdown_status_label.config(text="⏸️ Đã hủy")
        self.shutdown_countdown_label.config(text="")
        self.append_log("✓ Đã hủy hẹn giờ tắt máy")
    
    def _execute_shutdown(self):
        """Thực hiện tắt máy"""
        self.append_log("=" * 50)
        self.append_log("🛑 HẾT GIỜ - ĐANG TẮT MÁY...")
        self.append_log("=" * 50)
        
        # Stop worker first
        if self.worker:
            try:
                self.worker.stop()
            except:
                pass
        
        # Shutdown command for Windows
        import subprocess
        try:
            subprocess.run(['shutdown', '/s', '/t', '10'], check=True)
            self.append_log("✓ Máy sẽ tắt sau 10 giây...")
            messagebox.showinfo("Thông báo", "Máy sẽ tắt sau 10 giây!\nĐể hủy, chạy: shutdown /a")
        except Exception as e:
            self.append_log(f"⚠️ Lỗi khi tắt máy: {e}")
            messagebox.showerror("Lỗi", f"Không thể tắt máy: {e}")
