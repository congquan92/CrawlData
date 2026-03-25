import customtkinter as ctk
from tkinter import messagebox
from core.config import AppConfig

class ConfigTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.create_widgets()

    def create_widgets(self):
        config_frame = ctk.CTkFrame(self, fg_color="#1f1f20", corner_radius=15)
        config_frame.pack(padx=80, pady=40, fill="both", expand=True)

        ctk.CTkLabel(config_frame, text="CẤU HÌNH HỆ THỐNG", font=("Manrope", 24, "bold"), text_color="#54e98a").pack(pady=(30, 20))

        self.var_threads = ctk.StringVar(value=str(AppConfig.MAX_THREADS))
        self.var_years = ctk.StringVar(value=str(AppConfig.MAX_YEARS))
        self.var_timeout = ctk.StringVar(value=str(AppConfig.TIMEOUT))

        self._add_config_row(config_frame, "Số luồng (Max Threads)", self.var_threads)
        self._add_config_row(config_frame, "Số năm cho phép (Max Years)", self.var_years)
        self._add_config_row(config_frame, "Thời gian chờ (Timeout - giây)", self.var_timeout)

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
