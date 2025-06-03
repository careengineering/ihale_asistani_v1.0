@echo off
title Ihale Asistani Baslat

REM ✅ Sanal ortamı aktive et
call .\.venv\Scripts\activate.bat

REM ✅ PYTHONPATH ayarla
SET PYTHONPATH=.

echo.
echo Streamlit arayüzü başlatılıyor...
streamlit run app\streamlit_app.py

pause
