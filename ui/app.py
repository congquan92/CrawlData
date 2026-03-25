import customtkinter as ctk
import queue
import threading
from datetime import datetime
from tkinter import messagebox
from tkinter import ttk

from core.manager import ThreadManager
from core.config import AppConfig
from core.live_processor import LiveProcessor

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("dark")  # Giao diện Dark Mode (chuẩn Kinetic Architect)
ctk.set_default_color_theme("green")  # Theme màu xanh (phù hợp với màu primary)

class ScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH CỬA SỔ ---
        self.title("GiaVang.org Scraper Tool - Kinetic Architect")
        self.geometry("900x640")
        self.minsize(900, 640)
        
        # --- BIẾN TRẠNG THÁI ---
        self.total_tasks = 0
        self.completed_tasks = 0
        self.is_running = False

        # --- TẠO TABS ---
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_history = self.tabview.add("📊 Lịch Sử Crawl")
        self.tab_live = self.tabview.add("🔥 Trực Tiếp (Live)")
        self.tab_config = self.tabview.add("⚙️ Cài Đặt")

        self.create_history_widgets()
        self.create_live_widgets()
        self.create_config_widgets()

    # =======================================================
    # UI TAB 1: HISTORY CRAWL
    # =======================================================
    def create_history_widgets(self):
        self.tab_history.grid_columnconfigure(0, weight=4, uniform="col")
        self.tab_history.grid_columnconfigure(1, weight=5, uniform="col")
        self.tab_history.grid_rowconfigure(0, weight=1)

        # KHU VỰC THIẾT LẬP INPUT (LEFT COLUMN)
        self.frame_input = ctk.CTkFrame(self.tab_history, fg_color="#1f1f20", corner_radius=15)
        self.frame_input.grid(row=0, column=0, padx=(5, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_input, text="Cài đặt tham số", font=("Manrope", 20, "bold"), text_color="#54e98a").pack(pady=(20, 5), padx=20, anchor="w")
        ctk.CTkLabel(self.frame_input, text="Trích xuất dữ liệu lịch sử.", font=("Inter", 12), text_color="#bbcbbb").pack(pady=(0, 15), padx=20, anchor="w")
        
        # -- BASE URL --
        ctk.CTkLabel(self.frame_input, text="BASE URL", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, anchor="w")
        self.entry_url = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_url.insert(0, "https://giavang.org/trong-nuoc/pnj/lich-su")
        self.entry_url.pack(padx=20, pady=(0, 15), fill="x")
        
        # -- DATE RANGE --
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
        
        # -- EXPORT FILE --
        ctk.CTkLabel(self.frame_input, text="TÊN FILE CSV", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(padx=20, pady=(15, 0), anchor="w")
        self.entry_csv = ctk.CTkEntry(self.frame_input, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.entry_csv.insert(0, "export.csv")
        self.entry_csv.pack(padx=20, pady=(0, 20), fill="x")
        
        # -- START BUTTON --
        self.btn_start = ctk.CTkButton(self.frame_input, text="▶ BẮT ĐẦU CRAWL", font=("Inter", 13, "bold"), 
                                       height=50, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919", 
                                       corner_radius=8, command=self.start_crawling)
        self.btn_start.pack(padx=20, fill="x")

        # KHU VỰC KẾT QUẢ VÀ TIẾN TRÌNH (RIGHT COLUMN)
        self.frame_output = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        self.frame_output.grid(row=0, column=1, padx=(10, 5), pady=10, sticky="nsew")

        # -- PROGRESS SECTION --
        self.frame_progress = ctk.CTkFrame(self.frame_output, fg_color="#1f1f20", corner_radius=12)
        self.frame_progress.pack(fill="x", pady=(0, 15))
        
        self.lbl_progress_text = ctk.CTkLabel(self.frame_progress, text="GLOBAL PROGRESS", font=("Space Grotesk", 10, "bold"), text_color="#869486")
        self.lbl_progress_text.pack(padx=20, pady=(10, 0), anchor="w")
        
        self.lbl_progress_pct = ctk.CTkLabel(self.frame_progress, text="0%", font=("Manrope", 30, "bold"), text_color="#54e98a")
        self.lbl_progress_pct.pack(padx=20, anchor="w")
        
        self.progressbar = ctk.CTkProgressBar(self.frame_progress, height=6, progress_color="#54e98a", fg_color="#353436")
        self.progressbar.pack(padx=20, pady=(10, 20), fill="x")
        self.progressbar.set(0)

        # -- CONSOLE LOG SECTION --
        self.frame_log = ctk.CTkFrame(self.frame_output, fg_color="#0e0e0f", corner_radius=12, border_width=1, border_color="#1f1f20")
        self.frame_log.pack(fill="both", expand=True)

        log_header = ctk.CTkFrame(self.frame_log, height=35, fg_color="#1f1f20", corner_radius=12) 
        log_header.pack(fill="x", padx=1, pady=1)
        
        ctk.CTkLabel(log_header, text=">_ Console Output", font=("Space Grotesk", 11, "bold"), text_color="#bbcbbb").pack(padx=15, pady=5, anchor="w")

        self.textbox_log = ctk.CTkTextbox(self.frame_log, font=("Space Grotesk", 12), text_color="#e5e2e3", fg_color="transparent", wrap="word", state="disabled")
        self.textbox_log.pack(padx=10, pady=10, fill="both", expand=True)

    # =======================================================
    # UI TAB 2: LIVE CRAWL
    # =======================================================
    def create_live_widgets(self):
        # Thiết kế lại Layout: Hàng trên = Nút điều khiển, Hàng dưới = Bảng (Table)
        self.tab_live.grid_columnconfigure(0, weight=1)
        self.tab_live.grid_rowconfigure(0, weight=0)
        self.tab_live.grid_rowconfigure(1, weight=1)

        # TOP ROW: Các chức năng tải dữ liệu và xuất CSV
        self.live_top = ctk.CTkFrame(self.tab_live, fg_color="#1f1f20", corner_radius=15)
        self.live_top.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.live_top.grid_columnconfigure(0, weight=1)
        self.live_top.grid_columnconfigure(1, weight=1)

        # 1. Khu vực TẢI GIÁ
        fetch_frame = ctk.CTkFrame(self.live_top, fg_color="transparent")
        fetch_frame.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        
        ctk.CTkLabel(fetch_frame, text="URL TRANG LIVE", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.live_entry_url = ctk.CTkEntry(fetch_frame, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.live_entry_url.insert(0, AppConfig.LIVE_URL)
        self.live_entry_url.pack(pady=(5, 10), fill="x")

        self.btn_fetch_live = ctk.CTkButton(fetch_frame, text="↻ TẢI DỮ LIỆU BẢNG", font=("Inter", 13, "bold"),
                                            height=45, fg_color="#353436", hover_color="#2a2a2b", text_color="#54e98a",
                                            command=self.fetch_live_data)
        self.btn_fetch_live.pack(fill="x")
        
        self.lbl_live_update_time = ctk.CTkLabel(fetch_frame, text="Thời gian website: Chưa xác định", font=("Space Grotesk", 12), text_color="#bbcbbb")
        self.lbl_live_update_time.pack(pady=(10, 0))

        # 2. Khu vực XUẤT CSV
        export_frame = ctk.CTkFrame(self.live_top, fg_color="transparent")
        export_frame.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")

        ctk.CTkLabel(export_frame, text="TÊN FILE CSV", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.live_entry_csv = ctk.CTkEntry(export_frame, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.live_entry_csv.insert(0, "giavang_live.csv")
        self.live_entry_csv.pack(pady=(5, 10), fill="x")

        self.btn_export_live = ctk.CTkButton(export_frame, text="⬇ XUẤT CSV BẢNG", font=("Inter", 13, "bold"),
                                             height=45, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919",
                                             command=self.export_live_csv)
        self.btn_export_live.pack(fill="x")
        
        self.lbl_live_status = ctk.CTkLabel(export_frame, text="", font=("Inter", 12), text_color="#2ecc71")
        self.lbl_live_status.pack(pady=(10, 0))

        # BOTTOM ROW: BẢNG TREEVIEW
        self.live_bottom = ctk.CTkFrame(self.tab_live, fg_color="#0e0e0f", corner_radius=10, border_width=1, border_color="#3d4a3e")
        self.live_bottom.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Cấu hình giao diện bảng (Dark mode cho Treeview)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0e0e0f", foreground="#e5e2e3", rowheight=30, fieldbackground="#0e0e0f", borderwidth=0, font=("Inter", 12))
        style.map('Treeview', background=[('selected', '#2a2a2b')])
        style.configure("Treeview.Heading", background="#1f1f20", foreground="#54e98a", font=("Manrope", 11, "bold"), borderwidth=0)
        
        # Thanh trượt cuộn chuột (Scrollbar)
        tree_scroll_y = ctk.CTkScrollbar(self.live_bottom, orientation="vertical")
        tree_scroll_y.pack(side="right", fill="y")
        
        self.live_tree = ttk.Treeview(self.live_bottom, columns=("khu_vuc", "he_thong", "mua_vao", "ban_ra"), show="headings", yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.configure(command=self.live_tree.yview)
        
        # Định nghĩa tiêu đề cột
        self.live_tree.heading("khu_vuc", text="KHU VỰC", anchor="w")
        self.live_tree.heading("he_thong", text="THƯƠNG HIỆU / HỆ THỐNG", anchor="w")
        self.live_tree.heading("mua_vao", text="MUA VÀO", anchor="e")
        self.live_tree.heading("ban_ra", text="BÁN RA", anchor="e")
        
        # Định dạng cột
        self.live_tree.column("khu_vuc", width=120, anchor="w")
        self.live_tree.column("he_thong", width=250, anchor="w")
        self.live_tree.column("mua_vao", width=100, anchor="e")
        self.live_tree.column("ban_ra", width=100, anchor="e")
        
        self.live_tree.pack(fill="both", expand=True, padx=2, pady=2)


    # =======================================================
    # UI TAB 3: CONFIGURATION
    # =======================================================
    def create_config_widgets(self):
        config_frame = ctk.CTkFrame(self.tab_config, fg_color="#1f1f20", corner_radius=15)
        config_frame.pack(padx=80, pady=40, fill="both", expand=True)

        ctk.CTkLabel(config_frame, text="CẤU HÌNH HỆ THỐNG", font=("Manrope", 24, "bold"), text_color="#54e98a").pack(pady=(30, 20))

        # Khai báo String Variables thay vì int để người dùng gõ
        self.var_threads = ctk.StringVar(value=str(AppConfig.MAX_THREADS))
        self.var_years = ctk.StringVar(value=str(AppConfig.MAX_YEARS))
        self.var_timeout = ctk.StringVar(value=str(AppConfig.TIMEOUT))

        # Form configs
        self._add_config_row(config_frame, "Số luồng (Max Threads)", self.var_threads)
        self._add_config_row(config_frame, "Số năm cho phép (Max Years)", self.var_years)
        self._add_config_row(config_frame, "Thời gian chờ (Timeout - giây)", self.var_timeout)

        # Save Button
        ctk.CTkButton(config_frame, text="💾 LƯU CẤU HÌNH", font=("Inter", 13, "bold"),
                      height=45, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919",
                      command=self.save_config).pack(pady=40)

    def _add_config_row(self, parent, label_text, str_var):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=60, pady=10)
        ctk.CTkLabel(row, text=label_text, font=("Inter", 13), text_color="#bbcbbb", width=200, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, textvariable=str_var, width=100, justify="center", fg_color="#1b1b1c", border_color="#3d4a3e")
        entry.pack(side="right")

    def save_config(self):
        try:
            AppConfig.MAX_THREADS = int(self.var_threads.get())
            AppConfig.MAX_YEARS = int(self.var_years.get())
            AppConfig.TIMEOUT = int(self.var_timeout.get())
            messagebox.showinfo("Thành công", "Đã lưu cài đặt mới áp dụng cho các phiên tiếp theo!")
        except Exception as e:
            messagebox.showerror("Lỗi Cài Đặt", "Vui lòng chỉ nhập số nguyên!")


    # =======================================================
    # LOGIC CHO TAB LIVE
    # =======================================================
    def fetch_live_data(self):
        self.btn_fetch_live.configure(state="disabled", text="Đang tải..")
        
        # Xóa dữ liệu cũ trên bảng
        for row in self.live_tree.get_children():
            self.live_tree.delete(row)
            
        self.live_tree.insert("", "end", values=("", "Đang trích xuất dữ liệu, vui lòng đợi...", "", ""))

        live_url = self.live_entry_url.get().strip()

        threading.Thread(target=self._fetch_live_thread, args=(live_url,), daemon=True).start()

    def _fetch_live_thread(self, url):
        result = LiveProcessor.get_full_live_data(url)
        self.after(0, self._update_live_ui, result)

    def _update_live_ui(self, result):
        self.btn_fetch_live.configure(state="normal", text="↻ TẢI DỮ LIỆU HIỆN TẠI")
        
        for row in self.live_tree.get_children():
            self.live_tree.delete(row)

        if result["status"] == "success":
            self.lbl_live_update_time.configure(text=f"Thời gian website: {result['update_time']}")
            print(f"\n[LIVE FULL DATA] Cập nhật lúc: {result['update_time']}")
            
            for item in result["prices"]:
                khoi_khu_vuc = item["khu_vuc"]
                he_thong = item["he_thong"]
                mua_gia = item["mua_vao"]
                ban_gia = item["ban_ra"]
                
                # Chèn dòng mơi vào Table (Treeview)
                self.live_tree.insert("", "end", values=(khoi_khu_vuc, he_thong, mua_gia, ban_gia))
                print(f"[{khoi_khu_vuc}] {he_thong} -> Mua: {mua_gia} / Bán: {ban_gia}")
            print("-" * 50)
        else:
            self.live_tree.insert("", "end", values=("LỖI TRUY CẬP", result["message"], "", ""))

    def export_live_csv(self):
        csv_name = self.live_entry_csv.get().strip()
        if not csv_name:
            self.lbl_live_status.configure(text="Vui lòng nhập tên file CSV!", text_color="#ffb4ab")
            return
            
        self.btn_export_live.configure(state="disabled")
        self.lbl_live_status.configure(text="Đang xuất CSV...", text_color="#bbcbbb")
        
        live_url = self.live_entry_url.get().strip()
        
        threading.Thread(target=self._export_live_thread, args=(live_url, csv_name,), daemon=True).start()

    def _export_live_thread(self, url, csv_name):
        result = LiveProcessor.get_details_table(url)
        if result["status"] == "success":
            try:
                result["data"].to_csv(csv_name, index=False, encoding="utf-8-sig")
                msg = f"Đã lưu thành công: {csv_name}"
                color = "#2ecc71"
            except Exception as e:
                msg = f"Lỗi ghi file: {e}"
                color = "#ffb4ab"
        else:
            msg = f"Lỗi: {result['message']}"
            color = "#ffb4ab"
            
        self.after(0, self._finish_export_live_ui, msg, color)

    def _finish_export_live_ui(self, message, color):
        self.lbl_live_status.configure(text=message, text_color=color)
        self.btn_export_live.configure(state="normal")


    # =======================================================
    # LOGIC CHO TAB HISTORY
    # =======================================================
    def write_log(self, message):
         """In log ra Textbox Tab History"""
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
