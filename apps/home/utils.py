import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Path ke folder model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'ai_model')

# Load Model & Tokenizer secara Global (agar tidak berat saat dipanggil)
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    MODEL_LOADED = True
except Exception as e:
    print(f"Gagal memuat model AI: {e}")
    MODEL_LOADED = False

def get_sentiment_prediction(text):
    if not MODEL_LOADED or not text:
        return "Netral"
    
    # Tokenisasi
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    
    # Prediksi
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prediction = torch.argmax(probs, dim=-1).item()
    
    # Mapping label sesuai training di Colab Anda (0:Negatif, 1:Netral, 2:Positif)
    mapping = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}
    return mapping.get(prediction, "Netral")