import requests
from bs4 import BeautifulSoup
import pandas as pd

class CrawlProcessor:
    """Class xử lý tải HTML và parse dữ liệu bảng"""
    
    @staticmethod
    def parse_html(url):
        try:
            # Bắt lỗi timeout 10 giây cho từng request giả lập mạng chậm
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return {"status": "error", "message": f"Timeout khi tải {url}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi HTTP: {e}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm bảng dữ liệu trong cấu trúc trang
        table = soup.find('table')
        if not table:
            return {"status": "empty", "message": f"Không tìm thấy bảng dữ liệu tại {url}"}
            
        rows = table.find_all('tr')
        # Tối thiểu 1 dòng header, 1 dòng kết, 1 dòng data. Nếu <=2 coi như bảng trống
        if not rows or len(rows) <= 2:
            return {"status": "empty", "message": f"Bảng trống tại {url}"}

        data = []
        # Mapping để lưu trữ thông tin rowspan cua các ô ở dòng trước
        # Cấu trúc: {cell_index_của_cột: {'value': giá_trị, 'span': số_dòng_còn_lại}}
        rowspan_map = {}
        
        # Bỏ qua dòng header đầu tiên (index 0) và dòng tổng/ghi chú cuối cùng (index -1)
        # Giữ nguyên ý tưởng xử lý rowspan phức tạp
        for row_idx, row in enumerate(rows[1:-1]):  
            cells = row.find_all(['td', 'th'])
            row_data = []
            cell_idx = 0
            cell_ptr = 0 # Con trỏ duyệt các thẻ cell html trong dòng
            
            # Loop tổng quát cho đến khi lấy đủ giá trị cho cột
            while cell_ptr < len(cells) or cell_idx in rowspan_map:
                # 1. Khôi phục dữ liệu từ rowspan của các dòng trên nếu có tại vị trí này
                if cell_idx in rowspan_map and rowspan_map[cell_idx]['span'] > 0:
                    row_data.append(rowspan_map[cell_idx]['value'])
                    rowspan_map[cell_idx]['span'] -= 1
                    # Nếu span về 0, xóa khỏi map để giải phóng bộ nhớ (hoặc để mặc định update đè)
                    cell_idx += 1
                    continue
                
                # 2. Đọc cell hiện tại trong HTML
                if cell_ptr < len(cells):
                    cell = cells[cell_ptr]
                    text = cell.get_text(strip=True)
                    rowspan = int(cell.get('rowspan', 1))
                    
                    if rowspan > 1:
                        # Lưu giá trị và trừ đi 1 dòng hiện tại vừa tiêu thụ
                        rowspan_map[cell_idx] = {'value': text, 'span': rowspan - 1}
                        
                    row_data.append(text)
                    cell_idx += 1
                    cell_ptr += 1
                else:
                    break
                
            # Cấu trúc mong muốn: [khu_vuc, loai_vang, mua_vao, ban_ra, thoi_gian_cap_nhat]
            # Nếu dư cột thì cắt, hoặc lấy 5 cột đầu tiên
            if len(row_data) >= 5:
                data.append(row_data[:5])
        
        if not data:
            return {"status": "empty", "message": f"Không có dòng dữ liệu hợp lệ tại {url}"}
            
        # Tạo DataFrame chứa 5 cột theo yêu cầu kỹ thuật
        df = pd.DataFrame(data, columns=["khu_vuc", "loai_vang", "mua_vao", "ban_ra", "thoi_gian_cap_nhat"])
        return {"status": "success", "data": df}
