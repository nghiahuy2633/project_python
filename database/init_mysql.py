import os
import pandas as pd
import pymysql

BASE_DIR = os.path.dirname(__file__)

# SỬA: Đổi "Data" thành "data" viết thường cho đúng cấu trúc Git
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "books_clean.csv")

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="abc@123", # SỬA: Điền mật khẩu máy bạn vào đây
    database="fahasa_db",
    charset="utf8mb4"
)

cursor = conn.cursor()
df = pd.read_csv(CSV_PATH)

# Đóng gói mảng tuple để thực hiện Bulk Insert
data = list(df[[
    "id", "link", "title", "category_path", "author", 
    "publisher", "publish_year", "page_count", 
    "current_price", "old_price", "description"
]].itertuples(index=False, name=None))

sql = """
INSERT INTO books (
    id, link, title, category_path, author, 
    publisher, publish_year, page_count, 
    current_price, old_price, description
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""

print("[*] Đang nạp dữ liệu vào MySQL...")
cursor.executemany(sql, data)
conn.commit()

print(f"[+] Thành công! Đã nạp {len(data)} cuốn sách vào database local.")

cursor.close()
conn.close()