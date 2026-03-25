import concurrent.futures
import queue
from datetime import datetime, timedelta
import pandas as pd
from core.worker import CrawlWorker

class ThreadManager:
    """Class quản lý việc chia job và chạy các luồng"""
    
    def __init__(self, ui_controller):
        self.MAX_THREADS = 5
        self.ui_controller = ui_controller
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
    def generate_date_range(self, start_date, end_date):
        dates = []
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if end < start:
                raise ValueError("Ngày kết thúc nhỏ hơn ngày bắt đầu")
            delta = end - start
            for i in range(delta.days + 1):
                day = start + timedelta(days=i)
                dates.append(day.strftime("%Y-%m-%d"))
        except ValueError as e:
            self.log_queue.put(f"Lỗi cú pháp ngày: {e}")
            pass
        return dates
        
    def chunk_list(self, lst, n):
        """Chia mảng dates thành n chunks với số lượng phân bổ đều"""
        k, m = divmod(len(lst), n)
        return [lst[i*k+min(i, m) : (i+1)*k+min(i+1, m)] for i in range(n) if len(lst[i*k+min(i, m) : (i+1)*k+min(i+1, m)]) > 0]

    def run_spider(self, base_url, start_date, end_date, output_csv):
        dates = self.generate_date_range(start_date, end_date)
        if not dates:
            self.log_queue.put("Dừng tiến trình. Định dạng ngày không hợp lệ hoặc rỗng.")
            self.ui_controller.finish_crawling()
            return

        total_days = len(dates)
        self.ui_controller.set_total_tasks(total_days)
        self.log_queue.put(f"Tổng số ngày trong Queue: {total_days}")
        
        # Tối ưu: Nếu ít ngày thì chỉ cần dùng bấy nhiêu luồng, tối đa là MAX_THREADS
        actual_threads = min(self.MAX_THREADS, total_days)
        chunks = self.chunk_list(dates, actual_threads)
        
        all_dfs = []
        worker = CrawlWorker(self.log_queue, self.progress_queue)
        
        # Khởi chạy Thread Pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_THREADS) as executor:
            future_to_chunk = {
                executor.submit(worker.process_dates, f"Thread-{i+1}", base_url, chunk): chunk
                for i, chunk in enumerate(chunks)
            }
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                try:
                    df = future.result()
                    if not df.empty:
                        all_dfs.append(df)
                except Exception as exc:
                    self.log_queue.put(f"MỘT LUỒNG VĂNG LỖI CẤP CAO: {exc}")
                    
        # Kết thúc Thread Pool -> Gộp toàn bộ DataFrame lại
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            try:
                final_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
                self.log_queue.put(f"SUCCESS: Cứu dữ liệu thành công -> Xuất ra '{output_csv}' ({len(final_df)} dòng)")
            except Exception as e:
                self.log_queue.put(f"LỖI I/O KHI GHI FILE: {e}")
        else:
            self.log_queue.put("WARN: Không có bất kỳ dữ liệu DataFrame nào được lưu.")
            
        # Thông báo tới GUI
        self.ui_controller.finish_crawling()
