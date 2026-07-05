import os
import logging

# =====================================================================
# 🛠️ CẤU HÌNH CẤM GỌI INTERNET - ÉP CHẠY LOCAL THUẦN TÚY 100%
# =====================================================================
os.environ["HF_HUB_OFFLINE"] = "1"  # Chặn hoàn toàn việc kiểm tra token/update trực tuyến
logging.getLogger("huggingface_hub").setLevel(logging.ERROR) # Tắt sạch warning rác

import torch
import chromadb
from sentence_transformers import SentenceTransformer

# Tối ưu hóa luồng CPU cho máy cá nhân
torch.set_num_threads(4)

# Kết nối cơ sở dữ liệu Vector cục bộ
DB_PATH = os.path.join("data", "chroma_db")
CHROMA_CLIENT = chromadb.PersistentClient(path=DB_PATH)
COLLECTION = CHROMA_CLIENT.get_collection(name="fahasa_books")

# Biến toàn cục giữ mô hình trên RAM để tránh load lại nhiều lần
_MODEL_INSTANCE = None

def get_local_model():
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        print("[*] Đang nạp mô hình bge-m3 từ bộ nhớ Cache Local lên RAM...")
        # local_files_only=True: Ép thư viện chỉ đọc trong ổ cứng, không cần token xác thực
        _MODEL_INSTANCE = SentenceTransformer(
            'BAAI/bge-m3', 
            device='cpu', 
            local_files_only=True
        )
        _MODEL_INSTANCE.max_seq_length = 512
    return _MODEL_INSTANCE

def search_by_ai(query, top_k=10):
    """
    Hàm tìm kiếm ngữ nghĩa chạy hoàn toàn Offline trên CPU máy local.
    """
    if not query.strip():
        return []
        
    # 1. Sinh vector từ câu truy vấn ngay trên CPU
    model = get_local_model()
    query_vector = model.encode(query, show_progress_bar=False).tolist()
        
    # 2. Quét không gian vector trên ChromaDB cục bộ
    results = COLLECTION.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )
    
    # 3. Ép kiểu ID chuỗi về dạng số nguyên (INT) để khớp với MySQL của Thành viên 2
    raw_ids = results['ids'][0]
    return [int(x) for x in raw_ids]