import streamlit as st
import pandas as pd
import os

# ╔══════════════════════════════════════════════════════════════════╗
# ║  1. CẤU HÌNH TRANG VÀ DANH MỤC CỐ ĐỊNH                           ║
# ╚══════════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Fahasa Hybrid Search",
    page_icon="📖",
    layout="wide",
)

# Danh mục cấp 2 được bóc tách từ tập dữ liệu sạch để làm bộ lọc tĩnh trên UI
CATEGORIES = [
    "Tất cả", "Văn học", "Kinh tế", "Tâm lý - Kỹ năng sống", 
    "Thiếu nhi", "Sách Giáo Khoa - Tham Khảo", "Tiểu sử - Hồi ký", 
    "Sách Học Ngoại Ngữ", "Khoa Học Kỹ Thuật", "Tôn Giáo - Tâm Linh"
]
CAP_PRICE = 2_000_000  # Trần slider trên UI cho dễ dùng

st.title("📖 Hệ thống Tìm kiếm Sách Fahasa")
st.caption("Ứng dụng Tìm kiếm Lai: Kết hợp Sửa lỗi từ khóa (MySQL Mờ) và Tìm kiếm ngữ nghĩa sâu (AI Vector)")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  2. HÀM HIỂN THỊ LƯỚI SÁCH (Book Cards Grid)                      ║
# ╚══════════════════════════════════════════════════════════════════╝
PLACEHOLDER_IMG = "https://via.placeholder.com/160x220/f0f0f0/333333?text=📚"

def _fmt_title(text: str, max_len: int = 45) -> str:
    text = text or ""
    return text[:max_len] + ("…" if len(text) > max_len else "")

def _fmt_desc(text: str, max_len: int = 120) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text[:max_len] + ("…" if len(text) > max_len else "")

def display_book_grid(books_list: list, cols_per_row: int = 4) -> None:
    if not books_list:
        st.info("Không tìm thấy đầu sách nào phù hợp với điều kiện lọc.")
        return

    cols = st.columns(cols_per_row)
    for idx, book in enumerate(books_list):
        with cols[idx % cols_per_row]:
            st.image(PLACEHOLDER_IMG, width='stretch')
            st.markdown(f"**{_fmt_title(book.get('title', ''))}**")
            st.caption(f"✍️ {book.get('author', 'Không rõ tác giả')}")

            cur = int(book.get("current_price", 0) or 0)
            old = int(book.get("old_price", 0) or 0)
            pct = book.get("discount_percent", 0)

            if old > cur > 0:
                st.markdown(
                    f"<span style='color:#e74c3c;font-weight:700;font-size:15px'>{cur:,}đ</span>&nbsp;"
                    f"<span style='color:#999;text-decoration:line-through;font-size:12px'>{old:,}đ</span>&nbsp;"
                    f"<span style='background:#e74c3c;color:white;border-radius:4px;padding:1px 5px;font-size:11px'>-{int(pct)}%</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"<span style='color:#e74c3c;font-weight:700;font-size:15px'>{cur:,}đ</span>", unsafe_allow_html=True)

            st.caption(_fmt_desc(book.get("description", "")))
            st.link_button("🛒 Xem trên Fahasa", book.get("link", "#"))
            st.write("")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  3. CHIA TAB ĐIỀU KHIỂN GIAO DIỆN                                ║
# ╚══════════════════════════════════════════════════════════════════╝
tab1, tab2 = st.tabs(["🔍 Tìm kiếm thông thường", "🤖 Tìm kiếm bằng AI"])

# ── TAB 1: TÌM KIẾM TỪ KHÓA & BỘ LỌC ĐỘNG CỦA MYSQL ──
with tab1:
    col_filter, col_main = st.columns([1, 3], gap="large")

    with col_filter:
        st.subheader("🎯 Bộ lọc thuộc tính")
        category = st.selectbox("📂 Danh mục sách", CATEGORIES)
        
        # SỬA LOGIC GIÁ: Vì engine của Thành viên 2 dùng biến đơn 'max_price'
        # Nên giao diện chuyển sang slider 1 nút chọn mức giá tối đa để khớp 1-1.
        max_price_input = st.slider(
            "💰 Mức giá tối đa (đ)",
            min_value=0, max_value=CAP_PRICE,
            value=500_000, step=10_000, format="%d đ"
        )
        
        # (Tùy chọn phụ, hiện tại engine chưa xử lý sắp xếp và năm nên ta ẩn hoặc giữ làm mockup)
        sort_by = st.radio("↕️ Sắp xếp kết quả (Mock)", ["Mặc định", "Giá tăng dần", "Giá giảm dần"])
        limit_results = st.slider("📄 Số kết quả hiển thị", 4, 40, 12, 4)

    with col_main:
        search_query = st.text_input(
            "🔎 Nhập tên sách hoặc tên tác giả...",
            placeholder="Hỗ trợ gõ sai chính tả, không dấu (Ví dụ: dac nhan tam, nguyn nhat anh...)",
            key="mysql_search_input"
        )

        from engines.mysql_engine import search_by_keyword_and_filter
        
        # Chuẩn hóa giá trị Danh mục để truyền vào câu lệnh LIKE của MySQL
        category_param = None if category == "Tất cả" else category

        with st.spinner("Đang truy vấn cơ sở dữ liệu MySQL..."):
            # ĐÃ ĐỔI TÊN BIẾN KHỚP 1-1 VỚI FILE CỦA THÀNH VIÊN 2:
            # max_price, category, limit_results[cite: 4]
            books_to_show = search_by_keyword_and_filter(
                keyword=search_query,
                max_price=max_price_input,
                category=category_param,
                publish_year=None, # Tạm thời để trống theo cấu hình mặc định[cite: 4]
                limit_results=limit_results
            )
        
        total = len(books_to_show)
        if search_query.strip() or category != "Tất cả":
            if total == 0:
                st.warning(f"0 kết quả tìm thấy — Thử lại với từ khóa khác hoặc nới lỏng bộ lọc giá.")
            else:
                st.success(f"Tìm thấy {total:,} kết quả phù hợp thực tế!")
                display_book_grid(books_to_show)
        else:
            display_book_grid(books_to_show)

# ── TAB 2: TÌM KIẾM NGỮ NGHĨA SÂU BẰNG AI ──
with tab2:
    st.subheader("🤖 Tìm kiếm thông minh bằng AI Ngữ nghĩa")
    st.caption("Hệ thống tự động phân tích ý định, cảm xúc và ngữ cảnh thay vì khớp từng ký tự từ khóa cụ thể.")

    user_idea = st.text_area(
        "💡 Bạn đang tìm sách về chủ đề hay nội dung gì? (Viết tự do câu dài)",
        placeholder="Ví dụ: Tôi muốn đọc một cuốn sách giúp tôi vượt qua áp lực công việc, stress và tìm lại sự cân bằng...",
        height=120,
        key="ai_search_input"
    )

    col_a, _ = st.columns([1, 5])
    with col_a:
        top_k = st.selectbox("Số kết quả AI trả về", [4, 8, 12, 20], index=1, key="ai_top_k")

    if st.button("🤖 Kích hoạt AI quét Vector", type="primary", width='content'):
        if not user_idea.strip():
            st.warning("Vui lòng nhập mô tả ý tưởng/nhu cầu tìm sách của bạn.")
        else:
            with st.spinner("AI đang giải ma trận toán học và quét không gian ChromaDB..."):
                try:
                    # 1. Gọi lõi AI Engine để lấy mảng ID khớp nhất từ không gian vector
                    from engines.ai_engine import search_by_ai
                    matched_ids = search_by_ai(query=user_idea, top_k=top_k)
                    
                    # 2. Đưa mảng ID sang MySQL bốc thông tin chi tiết và giữ đúng thứ tự sắp xếp của AI
                    from engines.mysql_engine import fetch_books_by_ids
                    books_ai = fetch_books_by_ids(matched_ids)

                    if not books_ai:
                        st.warning("Không tìm thấy cuốn sách nào khớp với không gian ngữ nghĩa này.")
                    else:
                        st.success(f"Hệ thống AI đã bốc bộ lọc và trả về {len(books_ai)} cuốn sách tối ưu nhất!")
                        display_book_grid(books_ai)
                        
                except Exception as e:
                    st.error(f"❌ Đã xảy ra lỗi hệ thống trong tiến trình xử lý AI: {str(e)}")
                    