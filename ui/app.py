import customtkinter as ctk
import queue
import threading
from datetime import datetime
from core.manager import ThreadManager

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("dark")  # Giao diện Dark Mode (chuẩn Kinetic Architect)
ctk.set_default_color_theme("green")  # Theme màu xanh (phù hợp với màu primary)

class ScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH CỬA SỔ ---
        self.title("GiaVang.org Scraper Tool - By Kinetic Architect")
        self.geometry("900x620")
        self.minsize(900, 620)
        
        # --- BIẾN TRẠNG THÁI ---
        self.total_tasks = 0
        self.completed_tasks = 0
        self.is_running = False

        # --- TẠO VIEW ---
        self.create_widgets()
        
    def create_widgets(self):
        # 2 cột layout. Cột bên trái mỏng hơn (weight: 4), cột bên phải to (weight: 6)
        self.grid_columnconfigure(0, weight=4, uniform="col")
        self.grid_columnconfigure(1, weight=5, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        # =======================================================
        # KHU VỰC THIẾT LẬP INPUT (LEFT COLUMN)
        # =======================================================
        self.frame_input = ctk.CTkFrame(self, fg_color="#1f1f20", corner_radius=15)
        self.frame_input.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_input, text="Cài đặt tham số", font=("Manrope", 24, "bold"), text_color="#54e98a").pack(pady=(25, 5), padx=20, anchor="w")
        ctk.CTkLabel(self.frame_input, text="Configure target URL and date range.", font=("Inter", 12), text_color="#bbcbbb").pack(pady=(0, 25), padx=20, anchor="w")
        
        # -- BASE URL --
        ctk.CTkLabel(self.frame_input, text="BASE URL", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, anchor="w")
        self.entry_url = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_url.insert(0, "https://giavang.org")
        self.entry_url.pack(padx=20, pady=(0, 20), fill="x")
        
        # -- DATE RANGE --
        self.frame_dates = ctk.CTkFrame(self.frame_input, fg_color="transparent")
        self.frame_dates.pack(padx=20, pady=0, fill="x")
        self.frame_dates.grid_columnconfigure(0, weight=1)
        self.frame_dates.grid_columnconfigure(1, weight=1)
        
        self.frame_start = ctk.CTkFrame(self.frame_dates, fg_color="transparent")
        self.frame_start.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkLabel(self.frame_start, text="NGÀY BẮT ĐẦU", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.entry_start = ctk.CTkEntry(self.frame_start, height=45, font=("Inter", 13), placeholder_text="YYYY-MM-DD", fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_start.insert(0, "2024-01-01")
        self.entry_start.pack(fill="x")
        
        self.frame_end = ctk.CTkFrame(self.frame_dates, fg_color="transparent")
        self.frame_end.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(self.frame_end, text="NGÀY KẾT THÚC", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.entry_end = ctk.CTkEntry(self.frame_end, height=45, font=("Inter", 13), placeholder_text="YYYY-MM-DD", fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_end.insert(0, "2024-01-05")
        self.entry_end.pack(fill="x")
        
        # -- EXPORT FILE --
        ctk.CTkLabel(self.frame_input, text="TÊN FILE CSV", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, pady=(20, 0), anchor="w")
        self.entry_csv = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_csv.insert(0, "export.csv")
        self.entry_csv.pack(padx=20, pady=(0, 30), fill="x")
        
        # -- START BUTTON --
        # Bo góc lớn (corner_radius=8), màu xanh nổi bật active, gradient vibe
        self.btn_start = ctk.CTkButton(self.frame_input, text="▶ BẮT ĐẦU CRAWL", font=("Inter", 13, "bold"), 
                                       height=55, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919", 
                                       corner_radius=8, command=self.start_crawling)
        self.btn_start.pack(padx=20, fill="x")


        # =======================================================
        # KHU VỰC KẾT QUẢ VÀ TIẾN TRÌNH (RIGHT COLUMN)
        # =======================================================
        self.frame_output = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_output.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_output, text="Kết quả & Tiến trình", font=("Manrope", 24, "bold"), text_color="#e5e2e3").pack(pady=(0, 20), anchor="w")

        # -- PROGRESS SECTION --
        self.frame_progress = ctk.CTkFrame(self.frame_output, fg_color="#1f1f20", corner_radius=12)
        self.frame_progress.pack(fill="x", pady=(0, 20))
        
        # Header text
        self.lbl_progress_text = ctk.CTkLabel(self.frame_progress, text="GLOBAL PROGRESS", font=("Space Grotesk", 10, "bold"), text_color="#869486")
        self.lbl_progress_text.pack(padx=20, pady=(15, 0), anchor="w")
        
        # Center Number Box
        self.lbl_progress_pct = ctk.CTkLabel(self.frame_progress, text="0%", font=("Manrope", 34, "bold"), text_color="#54e98a")
        self.lbl_progress_pct.pack(padx=20, anchor="w")
        
        self.progressbar = ctk.CTkProgressBar(self.frame_progress, height=6, progress_color="#54e98a", fg_color="#353436")
        self.progressbar.pack(padx=20, pady=(15, 25), fill="x")
        self.progressbar.set(0)

        # -- CONSOLE LOG SECTION --
        self.frame_log = ctk.CTkFrame(self.frame_output, fg_color="#0e0e0f", corner_radius=12, border_width=1, border_color="#1f1f20")
        self.frame_log.pack(fill="both", expand=True)

        # Fake header for Console log
        log_header = ctk.CTkFrame(self.frame_log, height=40, fg_color="#1f1f20", corner_radius=12) 
        log_header.pack(fill="x", padx=1, pady=1)
        
        ctk.CTkLabel(log_header, text=">_ Console Output", font=("Space Grotesk", 11, "bold"), text_color="#bbcbbb").pack(padx=15, pady=8, anchor="w")

        self.textbox_log = ctk.CTkTextbox(self.frame_log, font=("Space Grotesk", 12), text_color="#e5e2e3",
                                          fg_color="transparent", wrap="word", state="disabled")
        self.textbox_log.pack(padx=10, pady=10, fill="both", expand=True)

    def write_log(self, message):
         """In log ra Textbox và tự động scroll-down"""
         self.textbox_log.configure(state="normal")
         timestamp = datetime.now().strftime("%H:%M:%S")
         self.textbox_log.insert("end", f"[{timestamp}] {message}\n")
         self.textbox_log.see("end")  # Tự động cuộn xuống dưới cùng
         self.textbox_log.configure(state="disabled")

    def set_total_tasks(self, total):
        """Khởi tạo biến đếm tổng cho Progress bar"""
        self.total_tasks = total
        self.completed_tasks = 0
        self.update_progress(0)

    def update_progress(self, completed_tasks):
        """Tính toán phần trăm và render UI Progress bar"""
        if self.total_tasks > 0:
             # Tính toán tỉ lệ % hoàn thành
            percentage = completed_tasks / self.total_tasks
            # Đảm bảo < 1.0 (Tránh lỗi scale UI)
            percentage = min(percentage, 1.0)
            self.progressbar.set(percentage)
            self.lbl_progress_pct.configure(text=f"{int(percentage * 100)}%")

    def process_queues(self):
        """
        Vòng lặp bất đồng bộ kiểm tra Data qua queues.
        Đảm bảo UI vẫn không bị Don't Responder khi render GUI.
        """
        if not self.is_running:
            return
            
        # Kiểm tra hàng đợi in log màn hình
        while not self.manager.log_queue.empty():
            try:
                msg = self.manager.log_queue.get_nowait()
                if msg:
                     self.write_log(msg)
            except queue.Empty:
                break
                
        # Kiểm tra hàng đợi update tiến độ
        while not self.manager.progress_queue.empty():
             try:
                 self.manager.progress_queue.get_nowait()
                 self.completed_tasks += 1
                 self.update_progress(self.completed_tasks)
             except queue.Empty:
                 break

        # Chạy trạm tuần hoàn check sau 100ms
        self.after(100, self.process_queues)

    def start_crawling(self):
        """Ham callback khi ấn 'Bắt đầu Crawl'"""
        if self.is_running:
            return
            
        base_url = self.entry_url.get().strip()
        start_date = self.entry_start.get().strip()
        end_date = self.entry_end.get().strip()
        csv_file = self.entry_csv.get().strip()

        if not all([base_url, start_date, end_date, csv_file]):
            self.write_log("LỖI: Bạn chưa điền đầy đủ các thông số.")
            return

        # Clear text cũ
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")
        
        self.btn_start.configure(state="disabled", text="[Đang xử lý...]", fg_color="#3d4a3e")
        self.is_running = True
        self.write_log("Khởi tạo hệ thống Kinetic Scraping Engine...")
        
        # Init Manager Thread Data
        self.manager = ThreadManager(ui_controller=self)
        
        # Start Master Crawler Daemon Thread (luồng chạy ngầm không khoá GUI Thread)
        threading.Thread(
            target=self.manager.run_spider, 
            args=(base_url, start_date, end_date, csv_file), 
            daemon=True
        ).start()
        
        # Bắt đầu vòng lới check trạng thái
        self.after(100, self.process_queues)

    def finish_crawling(self):
        """Hàm kích hoạt ngay sau khi Task Thread kết thúc"""
        # Time-out nhỏ để dọn dẹp list queue còn dở
        self.after(300, self._finalize_ui)
        
    def _finalize_ui(self):
        # Thông log còn sót trong Queue
        while not self.manager.log_queue.empty():
            self.write_log(self.manager.log_queue.get())
        
        self.is_running = False
        self.btn_start.configure(state="normal", text="▶ BẮT ĐẦU CRAWL", fg_color="#2ecc71")
        self.write_log("---------- TASK COMPLETE ----------")
