import os
import torch
import cv2
import re
import easyocr
import numpy as np
import base64
from ultralytics import YOLO
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from llama_cpp import Llama # Library untuk model Llama 3 GGUF Anda



# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENTIMENT_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'sentiment')
KTP_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'ktp', 'best.pt')
# Path ke file blob 4.34 GB Llama 3 yang Anda unduh
LLAMA_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'chatbot', 'llama-3-8b.gguf')

# --- LOAD MODELS (GLOBAL SINGLETON) ---
def load_models():
    models = {}
    try:
        # 1. Sentiment Model
        models['sentiment_tk'] = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_PATH)
        models['sentiment_md'] = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_PATH)
        
        # 2. YOLO KTP & OCR
        models['ktp_yolo'] = YOLO(KTP_MODEL_PATH)
        models['ocr_reader'] = easyocr.Reader(['id'], gpu=torch.cuda.is_available())
        
        # 3. Llama 3 Chatbot (Integrated)
        if os.path.exists(LLAMA_MODEL_PATH):
            models['chatbot'] = Llama(model_path=LLAMA_MODEL_PATH, n_ctx=2048, n_threads=4)
        
        print("Seluruh Model AI Berhasil Dimuat.")
        return models
    except Exception as e:
        print(f"Error Loading Models: {e}")
        return None

AI_MODELS = load_models()

# ==========================================
# 1. FUNGSI CHATBOT LLAMA 3 (NEW INTEGRATION)
# ==========================================
def get_chatbot_response(user_input):
    """Menghasilkan jawaban dari Llama 3 dengan konteks Dapur Margadana."""
    if 'chatbot' not in AI_MODELS:
        return "Chatbot sedang tidak aktif."
    
    prompt = f"System: Anda adalah asisten digital untuk program Makan Bergizi Gratis di Kota Tegal.\nUser: {user_input}\nAssistant:"
    
    output = AI_MODELS['chatbot'](
        prompt, 
        max_tokens=256, 
        stop=["User:", "\n"], 
        echo=False
    )
    return output['choices'][0]['text'].strip()

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
def get_sentiment(text):
    inputs = AI_MODELS['sentiment_tk'](text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = AI_MODELS['sentiment_md'](**inputs)
        prediction = torch.argmax(torch.nn.functional.softmax(outputs.logits, dim=-1), dim=-1).item()
    
    mapping = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
    return mapping.get(prediction, "Netral")