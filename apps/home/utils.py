import os
import torch
import cv2
import re
import easyocr
import numpy as np
from ultralytics import YOLO
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from llama_cpp import Llama 

# --- TAMBAHAN LIBRARY UNTUK RAG ---
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENTIMENT_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'sentiment')
KTP_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'ktp', 'best.pt')

# UPDATE: Menggunakan model 1B yang baru Anda unduh agar ringan di CPU
LLAMA_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'chatbot', 'Llama-3.2-1B-Instruct-Q4_K_M.gguf')

# UPDATE: Path ke Database Pengetahuan (RAG)
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'data', 'db_makan_bergizi')

# --- LOAD MODELS (GLOBAL SINGLETON) ---
def load_models():
    models = {} 
    try:
        # 1. Sentiment & YOLO KTP (Tetap Sama)
        models['sentiment_tk'] = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_PATH)
        models['sentiment_md'] = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_PATH)
        models['ktp_yolo'] = YOLO(KTP_MODEL_PATH)
        models['ocr_reader'] = easyocr.Reader(['id'], gpu=torch.cuda.is_available())
        
        # 2. Inisialisasi RAG (Embedding & Vector DB)
        embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        if os.path.exists(CHROMA_DB_PATH):
            models['vector_db'] = Chroma(
                persist_directory=CHROMA_DB_PATH, 
                embedding_function=embeddings
            )
            print("✅ Database Pengetahuan RAG Dimuat.")
        
        # 3. Llama 3.2 1B Chatbot
        if os.path.exists(LLAMA_MODEL_PATH):
            models['chatbot'] = Llama(
                model_path=LLAMA_MODEL_PATH, 
                n_ctx=2096,    # Optimasi RAM
                n_threads=4,   # Optimasi CPU
                verbose=False 
            )
            print("✅ Model Gizi Dimuat.")
        
        return models
    except Exception as e:
        print(f"Error Loading Models: {e}")
        return {}

AI_MODELS = load_models()

# ==========================================
# 1. FUNGSI CHATBOT DENGAN METODE RAG (UPDATED)
# ==========================================
def get_chatbot_response(user_input, chat_history=""):
    """
    Retrieval-Augmented Generation (RAG) dengan Persona Asisten MBG.
    Mendukung riwayat percakapan (memory) untuk konteks yang lebih baik.
    """
    # 1. Validasi Kesiapan Model
    if not AI_MODELS or 'chatbot' not in AI_MODELS or 'vector_db' not in AI_MODELS:
        return "Sistem informasi MBG sedang melakukan pemeliharaan data. Silakan coba sesaat lagi."

    try:
        # A. RETRIEVAL: Mencari informasi relevan dari database ChromaDB
        docs = AI_MODELS['vector_db'].similarity_search(user_input, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        # B. PROMPT ENGINEERING: Persona Resmi Asisten MBG
        # Menggunakan format header Llama 3/3.2 yang benar
        full_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
        Kamu adalah 'Asisten Digital Program Makan Bergizi Gratis (MBG)'. 
        Tugasmu adalah memberikan informasi yang akurat dan transparan mengenai program MBG.

        REFERENSI DATA:
        {context}

        RIWAYAT PERCAKAPAN TERAKHIR:
        {chat_history}

        Aturan:
        - Jawab secara profesional, santun, dan berbasis data referensi.
        - Jika informasi tidak ada di referensi, katakan Anda belum memiliki data tersebut secara sopan.
        - Gunakan Bahasa Indonesia yang baik dan benar.<|eot_id|><|start_header_id|>user<|end_header_id|>
        {user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

        # C. GENERATION: Llama 3.2 1B menyusun jawaban
        output = AI_MODELS['chatbot'](
            full_prompt, 
            max_tokens=512, 
            temperature=0.7, # Agar jawaban luwes tapi tetap fokus data
            echo=False
        )
        
        return output['choices'][0]['text'].strip()

    except Exception as e:
        print(f"RAG Error: {e}")
        return "Maaf, terjadi kendala teknis dalam memproses informasi MBG. Silakan hubungi admin."

    
# ==========================================
# 2. FUNGSI VERIFIKASI KTP (OPTIMIZED)
# ==========================================
def proses_verifikasi_ktp(img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"status": "error", "message": "Format gambar tidak didukung"}

    # LAPISAN 1: Deteksi Blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 80: # Threshold sedikit dilonggarkan agar tidak terlalu sensitif
        return {"status": "rejected", "message": "Foto terlalu buram"}

    # LAPISAN 2: YOLOv11 Detection
    results = AI_MODELS['ktp_yolo'].predict(source=img, conf=0.5, verbose=False)[0]
    
    if len(results.boxes) < 2:
        return {"status": "rejected", "message": "Komponen KTP tidak terdeteksi lengkap"}

    # EKSTRAKSI DATA
    hasil = {"nik": "Tidak terbaca", "nama": "Tidak terbaca"}
    for box in results.boxes:
        label = AI_MODELS['ktp_yolo'].names[int(box.cls[0])].lower()
        coords = box.xyxy[0].cpu().numpy().astype(int)
        crop = img[coords[1]:coords[3], coords[0]:coords[2]]

        if label == 'nik':
            ocr_res = AI_MODELS['ocr_reader'].readtext(crop, detail=0)
            text = "".join(ocr_res).upper()
            # Membersihkan kesalahan umum OCR pada angka
            text = text.replace('B', '6').replace('O', '0').replace('I', '1').replace('S', '5')
            nik_match = re.search(r'\d{16}', text)
            if nik_match: hasil['nik'] = nik_match.group(0)

        elif label == 'nama':
            ocr_res = AI_MODELS['ocr_reader'].readtext(crop, detail=0)
            hasil['nama'] = " ".join(ocr_res).replace(":", "").strip().upper()

    return {"status": "success", "data": hasil}

# ==========================================
# 3. ANALISIS SENTIMEN (EXISTING)
# ==========================================
def get_sentiment_prediction(text):
    inputs = AI_MODELS['sentiment_tk'](text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = AI_MODELS['sentiment_md'](**inputs)
        prediction = torch.argmax(torch.nn.functional.softmax(outputs.logits, dim=-1), dim=-1).item()
    
    mapping = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
    return mapping.get(prediction, "Netral")