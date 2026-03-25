import customtkinter as ctk

from ui.tabs.history_tab import HistoryTab
from ui.tabs.live_tab import LiveTab
from ui.tabs.config_tab import ConfigTab

# Cấu hình giao diện bản chuẩn của CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH CỬA SỔ ---
        self.title("Tool Crawl Dữ Liệu Giá Vàng")
        self.geometry("900x640")
        self.minsize(900, 640)
        
        # --- TẠO COMPONENT ---
        self.create_widgets()
        
    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
    
        self.tab_live_frame = self.tabview.add("🔥 Trực Tiếp (Live)")
        self.tab_history_frame = self.tabview.add("📊 Lịch Sử Crawl")
        self.tab_config_frame = self.tabview.add("⚙️ Cài Đặt")

        # Khởi tạo các class tương ứng đổ vào từng Frame trên TabView
        LiveTab(self.tab_live_frame).pack(fill="both", expand=True)
        HistoryTab(self.tab_history_frame).pack(fill="both", expand=True)
        ConfigTab(self.tab_config_frame).pack(fill="both", expand=True)
