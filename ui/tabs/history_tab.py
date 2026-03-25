import customtkinter as ctk
import queue
import threading
from datetime import datetime

from core.manager import ThreadManager
from core.config import AppConfig

class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.total_tasks = 0
        self.completed_tasks = 0
        self.is_running = False
        
        self.create_widgets()
        
    def create_widgets(self):
        self.grid_columnconfigure(0, weight=4, uniform="col")
        self.grid_columnconfigure(1, weight=5, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        # KHU VỰC THIẾT LẬP INPUT
        self.frame_input = ctk.CTkFrame(self, fg_color="#1f1f20", corner_radius=15)
        self.frame_input.grid(row=0, column=0, padx=(5, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_input, text="Cài đặt tham số", font=("Manrope", 20, "bold"), text_color="#54e98a").pack(pady=(20, 5), padx=20, anchor="w")
        ctk.CTkLabel(self.frame_input, text="Trích xuất dữ liệu lịch sử.", font=("Inter", 12), text_color="#bbcbbb").pack(pady=(0, 15), padx=20, anchor="w")
        
        ctk.CTkLabel(self.frame_input, text="BASE URL", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, anchor="w")
        self.entry_url = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_url.insert(0, "https://giavang.org/trong-nuoc/pnj/lich-su")
        self.entry_url.pack(padx=20, pady=(0, 15), fill="x")
        
        self.frame_dates = ctk.CTkFrame(self.frame_input, fg_color="transparent")
        self.frame_dates.pack(padx=20, pady=0, fill="x")
        self.frame_dates.grid_columnconfigure(0, weight=1)
        self.frame_dates.grid_columnconfigure(1, weight=1)
        
        self.frame_start = ctk.CTkFrame(self.frame_dates, fg_color="transparent")
        self.frame_start.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkLabel(self.frame_start, text="TỪ NGÀY", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.entry_start = ctk.CTkEntry(self.frame_start, height=45, font=("Inter", 13), placeholder_text="YYYY-MM-DD", fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_start.insert(0, "2024-01-01")
        self.entry_start.pack(fill="x")
        
        self.frame_end = ctk.CTkFrame(self.frame_dates, fg_color="transparent")
        self.frame_end.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(self.frame_end, text="ĐẾN NGÀY", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.entry_end = ctk.CTkEntry(self.frame_end, height=45, font=("Inter", 13), placeholder_text="YYYY-MM-DD", fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_end.insert(0, "2024-01-05")
        self.entry_end.pack(fill="x")
        
        ctk.CTkLabel(self.frame_input, text="TÊN FILE CSV", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, pady=(15, 0), anchor="w")
        self.entry_csv = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_csv.insert(0, "export.csv")
        self.entry_csv.pack(padx=20, pady=(0, 20), fill="x")
        
        self.btn_start = ctk.CTkButton(self.frame_input, text="▶ BẮT ĐẦU CRAWL", font=("Inter", 13, "bold"), 
                                       height=50, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919", 
                                       corner_radius=8, command=self.start_crawling)
        self.btn_start.pack(padx=20, fill="x")

        # KHU VỰC KẾT QUẢ
        self.frame_output = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_output.grid(row=0, column=1, padx=(10, 5), pady=10, sticky="nsew")

        self.frame_progress = ctk.CTkFrame(self.frame_output, fg_color="#1f1f20", corner_radius=12)
        self.frame_progress.pack(fill="x", pady=(0, 15))
        
        self.lbl_progress_text = ctk.CTkLabel(self.frame_progress, text="GLOBAL PROGRESS", font=("Space Grotesk", 10, "bold"), text_color="#869486")
        self.lbl_progress_text.pack(padx=20, pady=(10, 0), anchor="w")
        
        self.lbl_progress_pct = ctk.CTkLabel(self.frame_progress, text="0%", font=("Manrope", 30, "bold"), text_color="#54e98a")
        self.lbl_progress_pct.pack(padx=20, anchor="w")
        
        self.progressbar = ctk.CTkProgressBar(self.frame_progress, height=6, progress_color="#54e98a", fg_color="#353436")
        self.progressbar.pack(padx=20, pady=(10, 20), fill="x")
        self.progressbar.set(0)

        self.frame_log = ctk.CTkFrame(self.frame_output, fg_color="#0e0e0f", corner_radius=12, border_width=1, border_color="#1f1f20")
        self.frame_log.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(self.frame_log, height=35, fg_color="#1f1f20", corner_radius=12) 
        log_header.pack(fill="x", padx=1, pady=1)
        
        ctk.CTkLabel(log_header, text=">_ Console Output", font=("Space Grotesk", 11, "bold"), text_color="#bbcbbb").pack(padx=15, pady=5, anchor="w")

        self.textbox_log = ctk.CTkTextbox(self.frame_log, font=("Space Grotesk", 12), text_color="#e5e2e3", fg_color="transparent", wrap="word", state="disabled")
        self.textbox_log.pack(padx=10, pady=10, fill="both", expand=True)

    def write_log(self, message):
         self.textbox_log.configure(state="normal")
         timestamp = datetime.now().strftime("%H:%M:%S")
         self.textbox_log.insert("end", f"[{timestamp}] {message}\n")
         self.textbox_log.see("end")  
         self.textbox_log.configure(state="disabled")

    def set_total_tasks(self, total):
        self.total_tasks = total
        self.completed_tasks = 0
        self.update_progress(0)

    def update_progress(self, completed_tasks):
        if self.total_tasks > 0:
            percentage = completed_tasks / self.total_tasks
            percentage = min(percentage, 1.0)
            self.progressbar.set(percentage)
            self.lbl_progress_pct.configure(text=f"{int(percentage * 100)}%")

    def process_queues(self):
        if not self.is_running:
            return
            
        while not self.manager.log_queue.empty():
            try:
                msg = self.manager.log_queue.get_nowait()
                if msg: self.write_log(msg)
            except queue.Empty:
                break
                
        while not self.manager.progress_queue.empty():
             try:
                 self.manager.progress_queue.get_nowait()
                 self.completed_tasks += 1
                 self.update_progress(self.completed_tasks)
             except queue.Empty:
                 break

        self.after(100, self.process_queues)

    def start_crawling(self):
        if self.is_running: return
            
        base_url = self.entry_url.get().strip()
        start_date = self.entry_start.get().strip()
        end_date = self.entry_end.get().strip()
        csv_file = self.entry_csv.get().strip()

        if not all([base_url, start_date, end_date, csv_file]):
            self.write_log("LỖI: Bạn chưa điền đầy đủ các thông số.")
            return

        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")
        
        self.btn_start.configure(state="disabled", text="[Đang xử lý...]", fg_color="#3d4a3e")
        self.is_running = True
        self.write_log(f"Hệ thống đang chạy với tối đa {AppConfig.MAX_THREADS} luồng...")
        
        self.manager = ThreadManager(ui_controller=self)
        
        threading.Thread(
            target=self.manager.run_spider, 
            args=(base_url, start_date, end_date, csv_file), 
            daemon=True
        ).start()
        
        self.after(100, self.process_queues)

    def finish_crawling(self):
        self.after(300, self._finalize_ui)
        
    def _finalize_ui(self):
        while not self.manager.log_queue.empty():
            self.write_log(self.manager.log_queue.get())
        
        self.is_running = False
        self.btn_start.configure(state="normal", text="▶ BẮT ĐẦU CRAWL", fg_color="#2ecc71")
        self.write_log("---------- TASK COMPLETE ----------")
