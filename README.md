# 📖 FAHASA HYBRID SEARCH ENGINE

Dự án nghiên cứu và triển khai Hệ thống Tìm kiếm Lai (Hybrid Search) ứng dụng trên kho dữ liệu hơn 32,000 đầu sách từ nền tảng Fahasa. Hệ thống kết hợp tối ưu giữa phương thức tìm kiếm mờ sửa lỗi chính tả trên bộ nhớ RAM (MySQL + RapidFuzz) và tìm kiếm ngữ nghĩa chuyên sâu bằng mô hình Trí tuệ nhân tạo (AI Semantic Search với ChromaDB).

---

## 🏗️ CẤU TRÚC THƯ MỤC DỰ ÁN

```text
project_python/
│
├── data/
│   └── chroma_db/               # Cơ sở dữ liệu Vector của mô hình AI
│
├── engines/
│   ├── __init__.py
│   ├── ai_engine.py             # Động cơ xử lý Vector & Trích xuất ngữ nghĩa (Local Offline)
│   └── mysql_engine.py          # Động cơ truy vấn dữ liệu quan hệ & Tìm kiếm mờ (Fuzzy Search)
│
├── app.py                       # Giao diện điều khiển chính bằng Streamlit
└── requirements.txt             # Danh sách các thư viện phụ thuộc của hệ thống
```

## 💾 HƯỚNG DẪN KHỞI TẠO CƠ SỞ DỮ LIỆU (DATABASE SETUP)
Hệ thống sử dụng cấu trúc lưu trữ song song (Dual-Database) để phục vụ kiến trúc Tìm kiếm Lai:

1. Khởi tạo Cơ sở dữ liệu Quan hệ (MySQL)
Mở công cụ quản lý MySQL (như MySQL Workbench, Navicat hoặc DBeaver), tạo một database mới có tên là fahasa_db và chạy đoạn script SQL sau để khởi tạo cấu trúc bảng dữ liệu:
```SQL
CREATE DATABASE IF NOT EXISTS fahasa_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE fahasa_db;

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    current_price INT DEFAULT 0,
    old_price INT DEFAULT 0,
    category_path VARCHAR(500),
    description TEXT,
    link VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lưu ý: Sau khi tạo bảng, tiến hành Import file dữ liệu sạch (.sql hoặc .csv) 
-- chứa hơn 32,000 bản ghi sách vào bảng này.
```
2. Khởi tạo Cơ sở dữ liệu Không gian (ChromaDB Vector)
Thư mục lưu trữ cơ sở dữ liệu vector cục bộ được đặt cố định tại đường dẫn: data/chroma_db/.

Bạn không cần cài đặt phần mềm bên ngoài cho ChromaDB. Khi bạn khởi chạy ứng dụng lần đầu, file engines/ai_engine.py sẽ tự động kết nối và đọc tập hợp dữ liệu vector (Collection) tên là fahasa_books đã được định danh sẵn trong thư mục.

## ⚙️ HƯỚNG DẪN CÀI ĐẶT MÔI TRƯỜNG ẢO VÀ DỰ ÁN

Để đảm bảo các thư viện không bị xung đột phiên bản với hệ thống máy tính cá nhân, bạn triển khai môi trường ảo theo các bước thực tế dưới đây:

**Bước 1: Khởi tạo và kích hoạt môi trường ảo (Virtual Environment)**
Mở Terminal/Command Prompt tại thư mục gốc project_python/ và chạy các lệnh sau:

Trên Windows:
```
# 1. Tạo môi trường ảo có tên là venv
python -m venv venv

# 2. Kích hoạt môi trường ảo
.\venv\Scripts\activate
```
Trên macOS / Linux:
```
# 1. Tạo môi trường ảo có tên là venv
python3 -m venv venv

# 2. Kích hoạt môi trường ảo
source venv/bin/activate
```
Lưu ý: Sau khi kích hoạt thành công, bạn sẽ thấy chữ (venv) xuất hiện ở ngay đầu dòng lệnh của Terminal.

**Bước 2: Cài đặt các thư viện phụ thuộc**
Đảm bảo môi trường ảo vẫn đang được bật, chạy lệnh sau để tải và cấu hình toàn bộ gói thư viện cần thiết:
```
pip install torch --index-url [https://download.pytorch.org/ml/cpu](https://download.pytorch.org/ml/cpu)
pip install streamlit pymysql rapidfuzz sentence-transformers chromadb requests torchvision --no-deps
```
## 💻 HƯỚNG DẪN VẬN HÀNH ỨNG DỤNG

1. Cấu hình thông tin tài khoản kết nối
Mở file engines/mysql_engine.py.

Tìm hàm get_connection() và chỉnh sửa tham số password="MẬT_KHẨU_CỦA_BẠN" tương ứng với mật khẩu MySQL Server cục bộ trên máy tính của bạn.

2. Khởi chạy giao diện Tìm kiếm (Streamlit UI)
Tại Terminal đã kích hoạt venv, gõ lệnh:
```
streamlit run app.py
```
Hệ thống sẽ tự động khởi tạo server cục bộ và bật một tab mới trên trình duyệt web của bạn tại địa chỉ mặc định: http://localhost:8501.

3. Khởi chạy kịch bản Kiểm thử Hiệu năng (Performance Benchmarking)
Để đo đạc tốc độ phản hồi (Latency) thực tế của hệ thống phục vụ công tác làm số liệu cho báo cáo Word, chạy lệnh:
```
python run_performance_test.py
```
## 🛡️ TÍNH NĂNG VÀ ĐẶC ĐIỂM KỸ THUẬT NỔI BẬT
Tìm kiếm mờ (Tab 1): Tự động kích hoạt khi câu lệnh LIKE truyền thống thất bại. Sử dụng thuật toán fuzz.token_set_ratio của thư viện RapidFuzz để xử lý triệt để lỗi gõ sai chính tả, thiếu ký tự, thiếu dấu hoặc đảo thứ tự từ của người dùng ngay trên bộ nhớ RAM.

Tìm kiếm ngữ nghĩa (Tab 2): Hoạt động Offline 100%, loại bỏ hoàn toàn việc phụ thuộc vào kết nối mạng Internet hay mã xác thực Token trực tuyến. Ứng dụng mô hình BAAI/bge-m3 mã hóa cấu trúc ngữ cảnh câu lệnh tự do của người dùng để truy vấn không gian vector trên ChromaDB.
