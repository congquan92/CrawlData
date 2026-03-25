import requests
import pandas as pd
from bs4 import BeautifulSoup
from core.config import AppConfig

class LiveProcessor:
    """Class đảm nhận việc trích xuất dữ liệu đang trực tiếp xảy ra trên giavang.org"""
    
    @staticmethod
    def get_summary(url=None):
        if url is None:
            url = AppConfig.LIVE_URL
            
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=AppConfig.TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Timeout khi tải trang live."}
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {e}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        results = {}

        # Lấy các box giá vàng chính
        gold_boxes = soup.select("div.gold-price-box")
        for box in gold_boxes:
            current_title = None
            for tag in box.find_all(["h2", "div"], recursive=False):
                if tag.name == "h2":
                    current_title = tag.get_text(" ", strip=True)
                elif tag.name == "div" and "row" in tag.get("class", []):
                    cols = tag.select("div.col-6")
                    if len(cols) == 2 and current_title:
                        buy = cols[0].select_one(".gold-price")
                        sell = cols[1].select_one(".gold-price")
                        results[current_title] = {
                            "mua_vao": buy.get_text(" ", strip=True) if buy else "0",
                            "ban_ra": sell.get_text(" ", strip=True) if sell else "0",
                        }

        # Thời gian cập nhật
        update_tag = soup.select_one("h1.box-headline small")
        update_time = update_tag.get_text(" ", strip=True) if update_tag else "Không xác định"

        if not results:
             return {"status": "error", "message": "Không tìm thấy dữ liệu tóm tắt trên trang."}

        return {"status": "success", "update_time": update_time, "prices": results}

    @staticmethod
    def get_full_live_data(url=None):
        """Hàm gộp: Lấy thời gian cập nhật VÀ parse toàn bộ bảng chi tiết"""
        if url is None:
            url = AppConfig.LIVE_URL
            
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=AppConfig.TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Timeout khi tải trang live."}
        except Exception as e:
            return {"status": "error", "message": f"Connection error: {e}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 1. Update time
        update_tag = soup.select_one("h1.box-headline small")
        update_time = update_tag.get_text(" ", strip=True) if update_tag else "Không xác định"

        # 2. Table Data
        table = soup.find("table", class_="table")
        if not table:
            return {"status": "empty", "message": "Không tìm thấy bảng giá vàng."}

        tbody = table.find("tbody")
        if not tbody:
            return {"status": "empty", "message": "Không tìm thấy tbody trong bảng."}

        rows = tbody.find_all("tr")
        data = []
        current_khu_vuc = None

        for row in rows:
            cols_th = row.find_all("th")
            cols_td = row.find_all("td")

            # bỏ dòng footer cập nhật
            if len(cols_td) == 1 and cols_td[0].get("colspan") == "4":
                continue

            if len(cols_th) == 1 and len(cols_td) == 3:
                current_khu_vuc = cols_th[0].get_text(" ", strip=True)
                he_thong = cols_td[0].get_text(" ", strip=True)
                mua = cols_td[1].get_text(" ", strip=True)
                ban = cols_td[2].get_text(" ", strip=True)
            elif len(cols_th) == 0 and len(cols_td) == 3:
                if not current_khu_vuc:
                    continue
                he_thong = cols_td[0].get_text(" ", strip=True)
                mua = cols_td[1].get_text(" ", strip=True)
                ban = cols_td[2].get_text(" ", strip=True)
            else:
                continue

            data.append({
                "khu_vuc": current_khu_vuc,
                "he_thong": he_thong,
                "mua_vao": mua,
                "ban_ra": ban
            })
            
        if not data:
            return {"status": "empty", "message": "Bảng không có dữ liệu."}

        return {"status": "success", "update_time": update_time, "prices": data}

    @staticmethod
    def get_details_table(url=None):
        if url is None:
            url = AppConfig.LIVE_URL
            
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=AppConfig.TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
             return {"status": "error", "message": f"Lỗi: {e}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="table")
        if not table:
            return {"status": "empty", "message": "Không tìm thấy bảng giá vàng."}

        tbody = table.find("tbody")
        if not tbody:
            return {"status": "empty", "message": "Không tìm thấy tbody trong bảng."}

        rows = tbody.find_all("tr")
        data = []
        current_khu_vuc = None

        def parse_number(text: str) -> int:
            try:
                return int(text.strip().replace(".", ""))
            except:
                return 0

        for row in rows:
            cols_th = row.find_all("th")
            cols_td = row.find_all("td")

            # bỏ dòng footer cập nhật
            if len(cols_td) == 1 and cols_td[0].get("colspan") == "4":
                continue

            # Dòng chứa Khu Vực
            if len(cols_th) == 1 and len(cols_td) == 3:
                current_khu_vuc = cols_th[0].get_text(" ", strip=True)
                he_thong = cols_td[0].get_text(" ", strip=True)
                mua_vao = cols_td[1].get_text(" ", strip=True)
                ban_ra = cols_td[2].get_text(" ", strip=True)

            # Các dòng tiếp theo cùng Khu Vực
            elif len(cols_th) == 0 and len(cols_td) == 3:
                if not current_khu_vuc:
                    continue
                he_thong = cols_td[0].get_text(" ", strip=True)
                mua_vao = cols_td[1].get_text(" ", strip=True)
                ban_ra = cols_td[2].get_text(" ", strip=True)

            else:
                continue

            data.append({
                "khu_vuc": current_khu_vuc,
                "he_thong": he_thong,
                "mua_vao_x1000": parse_number(mua_vao),
                "ban_ra_x1000": parse_number(ban_ra),
                "mua_vao_vnd": parse_number(mua_vao) * 1000,
                "ban_ra_vnd": parse_number(ban_ra) * 1000,
            })

        if not data:
            return {"status": "empty", "message": "Bảng không có dữ liệu để xuất CSV."}
            
        return {"status": "success", "data": pd.DataFrame(data)}
