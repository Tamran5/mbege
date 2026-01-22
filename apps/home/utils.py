import os
import torch
import cv2
import re
import easyocr
import numpy as np
from ultralytics import YOLO
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --- KONFIGURASI PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENTIMENT_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'sentiment')
KTP_MODEL_PATH = os.path.join(BASE_DIR, 'ai_model', 'ktp', 'best.pt')

# --- LOAD MODEL SENTIMEN (GLOBAL) ---
try:
    tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_PATH)
    sentiment_model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_PATH)
    SENTIMENT_LOADED = True
except Exception as e:
    print(f"Gagal memuat model Sentimen: {e}")
    SENTIMENT_LOADED = False

# --- LOAD MODEL KTP & OCR (GLOBAL) ---
try:
    model_ktp = YOLO(KTP_MODEL_PATH)
    reader = easyocr.Reader(['id'])
    KTP_LOADED = True
except Exception as e:
    print(f"Gagal memuat model KTP/OCR: {e}")
    KTP_LOADED = False

# ==========================================
# 1. FUNGSI ANALISIS SENTIMEN (EXISTING)
# ==========================================
def get_sentiment_prediction(text):
    if not SENTIMENT_LOADED or not text:
        return "Netral"
    
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    
    with torch.no_grad():
        outputs = sentiment_model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prediction = torch.argmax(probs, dim=-1).item()
    
    mapping = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
    return mapping.get(prediction, "Netral")

# ==========================================
# 2. FUNGSI VERIFIKASI KTP (NEW)
# ==========================================
def proses_verifikasi_ktp(img_bytes):
    """
    Fungsi utama untuk memproses gambar KTP dari Flutter.
    Menangani: Blur, Bukan KTP, dan Ekstraksi Data.
    """
    # 1. Konversi bytes ke format OpenCV
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"status": "error", "message": "Format gambar tidak didukung"}

    # 2. LAPISAN 1: Deteksi Blur (PCD Logic)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Threshold 100 (bisa disesuaikan, makin tinggi makin ketat)
    if laplacian_var < 100:
        return {
            "status": "rejected", 
            "message": "Foto terlalu buram, silakan ambil foto ulang dengan cahaya cukup"
        }

    # 3. LAPISAN 2: Jalankan YOLOv11
    results = model_ktp.predict(source=img, conf=0.6, verbose=False)[0]
    
    # 4. LAPISAN 3: Logika Penolakan (Bukan KTP)
    # KTP asli harus memiliki minimal komponen utama (misal: NIK, Nama, Foto, dsb)
    # Jika terdeteksi kurang dari 3 komponen, anggap bukan KTP
    if len(results.boxes) < 3:
        return {
            "status": "rejected", 
            "message": "Gambar tidak dikenali sebagai KTP. Pastikan seluruh kartu terlihat jelas."
        }

    # 5. EKSTRAKSI DATA (Jika lolos validasi)
    hasil_ekstraksi = {"nik": "Tidak terbaca", "nama": "Tidak terbaca"}
    
    for box in results.boxes:
        label = model_ktp.names[int(box.cls[0])].lower()
        coords = box.xyxy[0].cpu().numpy().astype(int)
        
        # Crop area deteksi untuk OCR
        crop = img[coords[1]:coords[3], coords[0]:coords[2]]

        if label == 'nik':
            ocr_res = reader.readtext(crop, detail=0)
            text_nik = "".join(ocr_res).replace(" ", "").replace(":", "")
            # Validasi Regex: Harus 16 digit
            match = re.search(r'\d{16}', text_nik)
            if match:
                hasil_ekstraksi['nik'] = match.group(0)

        elif label == 'nama':
            ocr_res = reader.readtext(crop, detail=0)
            # Membersihkan teks nama dari karakter aneh
            nama_clean = " ".join(ocr_res).replace(":", "").strip()
            hasil_ekstraksi['nama'] = nama_clean

    return {
        "status": "success", 
        "data": hasil_ekstraksi
    }