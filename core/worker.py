import pandas as pd
import time
from core.processor import CrawlProcessor

class CrawlWorker:
    """Class luồng xử lý nhận một mảng các ngày và cào dữ liệu"""
    
    def __init__(self, log_queue, progress_queue, stop_event=None):
        self.log_queue = log_queue
        self.progress_queue = progress_queue
        self.stop_event = stop_event

    def process_dates(self, thread_name, base_url, dates):
        all_data = []
        for date_str in dates:
            if self.stop_event and self.stop_event.is_set():
                self.log_queue.put(f"[{thread_name}] Tiến trình đã bị dừng bởi người dùng.")
                break
            # Ví dụ: https://giavang.org/trong-nuoc/pnj/lich-su/YYYY-MM-DD.html
            url = f"{base_url.rstrip('/')}/{date_str}.html"
            self.log_queue.put(f"[{thread_name}] Đang crawl {date_str}...")
            
            result = CrawlProcessor.parse_html(url)
            
            if result["status"] == "success":
                df = result["data"]
                df["ngay_gia_vang"] = date_str # Thêm cột theo dõi ngày
                all_data.append(df)
                self.log_queue.put(f"[{thread_name}] Thành công: {date_str} ({len(df)} dòng)")
            elif result["status"] == "empty":
                self.log_queue.put(f"[{thread_name}] Bỏ qua ngày {date_str}: {result['message']}")
            else:
                self.log_queue.put(f"[{thread_name}] Thất bại tại {date_str}: {result['message']}")
            
            # Cập nhật tiến độ hoàn thành 1 ngày về GUI
            self.progress_queue.put(1)
            time.sleep(0.5) # Time sleep mềm để tránh ăn block 429 từ máy chủ web
            
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
