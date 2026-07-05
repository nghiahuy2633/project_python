import pymysql
from rapidfuzz import process, fuzz

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="abc@123",
        database="fahasa_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def search_by_keyword_and_filter(
    keyword="",
    max_price=None,
    category=None,
    publish_year=None,
    limit_results=12
):
    conn = get_connection()
    # cursor = conn.cursor()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # --- BƯỚC 1: LỌC DỮ LIỆU CỨNG (Theo giá, danh mục, năm xuất bản nếu có) ---
    sql_base = "SELECT * FROM books WHERE 1=1"
    params_base = []

    if max_price is not None:
        sql_base += " AND current_price <= %s"
        params_base.append(max_price)

    if category:
        sql_base += " AND category_path LIKE %s"
        params_base.append(f"%{category}%")

    if publish_year:
        sql_base += " AND publish_year = %s"
        params_base.append(publish_year)


    # --- BƯỚC 2: TIẾN HÀNH TÌM KIẾM THEO TỪ KHÓA ---
    keyword = keyword.strip()
    
    if not keyword:
        # Nếu người dùng không nhập từ khóa, chỉ lọc theo các điều kiện trên
        sql_base += " LIMIT %s"
        params_base.append(limit_results)
        cursor.execute(sql_base, params_base)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result

    # KẾ HOẠCH A: Thử tìm chính xác tương đối bằng LIKE trước
    sql_like = sql_base + " AND (title LIKE %s OR author LIKE %s) LIMIT %s"
    params_like = params_base + [f"%{keyword}%", f"%{keyword}%", limit_results]
    
    cursor.execute(sql_like, params_like)
    exact_results = cursor.fetchall()

    # Nếu có kết quả bằng LIKE, trả về ngay lập tức (Rất nhanh, nhẹ máy)
    if exact_results:
        cursor.close()
        conn.close()
        return exact_results


    # KẾ HOẠCH B: Nếu LIKE trả về 0 kết quả -> Kích hoạt tìm kiếm mờ (Fuzzy Search)
    print(f"[Fuzzy Search] Kích hoạt tìm kiếm mờ cho từ khóa: '{keyword}'")
    
    # Lấy toàn bộ sách thỏa mãn bộ lọc cứng về RAM để quét mờ
    cursor.execute(sql_base, params_base)
    all_filtered_books = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not all_filtered_books:
        return []

    # Chuẩn bị danh sách chuỗi gộp (Tiêu đề + Tác giả) để thuật toán so khớp
    search_targets = []
    for book in all_filtered_books:
        title = str(book.get('title', '')).strip()
        author = str(book.get('author', '')).strip() if book.get('author') else ""
        search_targets.append(f"{title} {author}")

    # Sử dụng rapidfuzz để chấm điểm độ tương đồng
    # score_cutoff=50.0: Điểm trên 50 mới lấy (gõ sai vài ký tự vẫn nhận)
    fuzzy_matches = process.extract(
        keyword,
        search_targets,
        scorer=fuzz.token_set_ratio, # Cực mạnh với việc gõ thiếu dấu hoặc đảo từ
        limit=limit_results,
        score_cutoff=50.0
    )

    # Trích xuất lại các cuốn sách tương ứng dựa trên index đã khớp
    fuzzy_books = []
    for match in fuzzy_matches:
        matched_index = match[2] # Vị trí index trong mảng search_targets
        fuzzy_books.append(all_filtered_books[matched_index])

    return fuzzy_books

def fetch_books_by_ids(ids):
    """
    HÀM BỔ SUNG: Nhận mảng ID từ AI, bốc dữ liệu từ MySQL và giữ nguyên thứ tự sắp xếp.
    """
    if not ids:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # Tạo chuỗi placeholder kiểu "%s, %s, %s" tương ứng với số lượng ID
    placeholders = ",".join(["%s"] * len(ids))
    
    # Sử dụng ORDER BY FIELD để ép MySQL trả về dữ liệu đúng thứ tự mảng truyền vào
    sql = f"""
    SELECT *, ROUND(((old_price - current_price) / old_price) * 100) as discount_percent
    FROM books
    WHERE id IN ({placeholders})
    ORDER BY FIELD(id, {placeholders})
    """

    # Truyền danh sách ids hai lần vì có 2 cụm placeholders trong câu lệnh SQL
    cursor.execute(sql, ids + ids)
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result