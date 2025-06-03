@echo off
title Ihale Asistani Baslat

REM ✅ Sanal ortamı aktive et
call .\.venv\Scripts\activate.bat

REM ✅ PYTHONPATH ayarla
SET PYTHONPATH=.

echo.
echo [1/3] Ön işleme başlatılıyor...
python -c "from src.data_preprocessing import preprocess_raw_mevzuat; preprocess_raw_mevzuat('data/raw', 'data/processed')"

echo.
echo [2/3] Embedding dosyaları oluşturuluyor...
python -c "from src.embedder import generate_embeddings_from_processed; generate_embeddings_from_processed('data/processed', 'data/embeddings/ihale_embeddings.pkl')"

echo.
echo [3/3] Streamlit arayüzü başlatılıyor...
streamlit run app\streamlit_app.py

pause
