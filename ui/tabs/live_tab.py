import customtkinter as ctk
import threading
from tkinter import ttk
from core.config import AppConfig
from core.live_processor import LiveProcessor
from core.processor import CrawlProcessor

class LiveTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # TOP ROW: Controls
        self.live_top = ctk.CTkFrame(self, fg_color="#1f1f20", corner_radius=15)
        self.live_top.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.live_top.grid_columnconfigure(0, weight=1)
        self.live_top.grid_columnconfigure(1, weight=1)

        # Left controls
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

        # Right controls
        export_frame = ctk.CTkFrame(self.live_top, fg_color="transparent")
        export_frame.grid(row=0, column=1, padx=20, pady=15, sticky="nsew")

        ctk.CTkLabel(export_frame, text="TÊN FILE CSV", font=("Space Grotesk", 10, "bold"), text_color="#869486").pack(anchor="w")
        self.live_entry_csv = ctk.CTkEntry(export_frame, height=45, font=("Inter", 13), fg_color="#1b1b1c", border_color="#3d4a3e")
        self.live_entry_csv.insert(0, "giavang_hientai.csv")
        self.live_entry_csv.pack(pady=(5, 10), fill="x")

        self.btn_export_live = ctk.CTkButton(export_frame, text="⬇ XUẤT CSV BẢNG", font=("Inter", 13, "bold"),
                                             height=45, fg_color="#2ecc71", hover_color="#54e98a", text_color="#003919",
                                             command=self.export_live_csv)
        self.btn_export_live.pack(fill="x")
        
        self.lbl_live_status = ctk.CTkLabel(export_frame, text="", font=("Inter", 12), text_color="#2ecc71")
        self.lbl_live_status.pack(pady=(10, 0))

        # BOTTOM ROW: Treeview Board
        self.live_bottom = ctk.CTkFrame(self, fg_color="#0e0e0f", corner_radius=10, border_width=1, border_color="#3d4a3e")
        self.live_bottom.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0e0e0f", foreground="#e5e2e3", rowheight=30, fieldbackground="#0e0e0f", borderwidth=0, font=("Inter", 12))
        style.map('Treeview', background=[('selected', '#2a2a2b')])
        style.configure("Treeview.Heading", background="#1f1f20", foreground="#54e98a", font=("Manrope", 11, "bold"), borderwidth=0)
        
        tree_scroll_y = ctk.CTkScrollbar(self.live_bottom, orientation="vertical")
        tree_scroll_y.pack(side="right", fill="y")
        
        self.live_tree = ttk.Treeview(self.live_bottom, columns=("khu_vuc", "he_thong", "mua_vao", "ban_ra"), show="headings", yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.configure(command=self.live_tree.yview)
        
        self.live_tree.heading("khu_vuc", text="KHU VỰC", anchor="w")
        self.live_tree.heading("he_thong", text="THƯƠNG HIỆU / HỆ THỐNG", anchor="w")
        self.live_tree.heading("mua_vao", text="MUA VÀO", anchor="e")
        self.live_tree.heading("ban_ra", text="BÁN RA", anchor="e")
        
        self.live_tree.column("khu_vuc", width=120, anchor="w")
        self.live_tree.column("he_thong", width=250, anchor="w")
        self.live_tree.column("mua_vao", width=100, anchor="e")
        self.live_tree.column("ban_ra", width=100, anchor="e")
        
        self.live_tree.pack(fill="both", expand=True, padx=2, pady=2)


    # LOGIC CHO TAB LIVE
    def fetch_live_data(self):
        self.btn_fetch_live.configure(state="disabled", text="Đang tải..")
        
        for row in self.live_tree.get_children():
            self.live_tree.delete(row)
            
        self.live_tree.insert("", "end", values=("", "Đang trích xuất dữ liệu, vui lòng đợi...", "", ""))
        live_url = self.live_entry_url.get().strip()

        threading.Thread(target=self._fetch_live_thread, args=(live_url,), daemon=True).start()

    def _fetch_live_thread(self, url):
        result = LiveProcessor.get_full_live_data(url)
        
        if result["status"] in ("empty", "error"):
            raw = CrawlProcessor.parse_html(url)
            if raw["status"] == "success":
                df = raw["data"]
                data = []
                update_time = df.iloc[0]["thoi_gian_cap_nhat"] if (not df.empty and "thoi_gian_cap_nhat" in df.columns) else "Trích xuất lịch sử"
                
                for _, row in df.iterrows():
                    data.append({
                        "khu_vuc": row.get("khu_vuc", ""),
                        "he_thong": row.get("loai_vang", ""),
                        "mua_vao": row.get("mua_vao", ""),
                        "ban_ra": row.get("ban_ra", "")
                    })
                result = {"status": "success", "update_time": update_time, "prices": data}
            elif raw["status"] != "empty":
                # Nếu LiveProcessor rỗng nhưng CrawlProcessor lỗi thực sự thì lấy lỗi của Crawl
                result = raw
                
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
        
        if result["status"] in ("empty", "error"):
            raw = CrawlProcessor.parse_html(url)
            if raw["status"] == "success":
                result = raw
        
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
