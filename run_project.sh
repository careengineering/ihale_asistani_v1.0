#!/bin/bash

# İhale Asistanı projesini çalıştırmak için betik

# Sanal ortam kontrolü ve aktivasyonu
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Hata: Sanal ortam bulunamadı: $VENV_DIR"
    echo "Sanal ortam oluşturmak için: python3 -m venv $VENV_DIR"
    exit 1
fi

# Platforma göre aktivasyon dosyasını belirle
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || -d "$VENV_DIR/Scripts" ]]; then
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
else
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
fi

echo "Sanal ortam etkinleştiriliyor..."
if [ -f "$ACTIVATE_SCRIPT" ]; then
    source "$ACTIVATE_SCRIPT" || { echo "Hata: Sanal ortam etkinleştirilemedi"; exit 1; }
else
    echo "Hata: Aktivasyon betiği bulunamadı: $ACTIVATE_SCRIPT"
    echo "Sanal ortamı yeniden oluşturmayı deneyin: python3 -m venv $VENV_DIR"
    exit 1
fi


# Verileri işle
echo "Veriler işleniyor..."
python3 src/data_preprocessing.py || { echo "Hata: Veri işleme başarısız. Python sürümünü ve bağımlılıkları kontrol edin."; deactivate; exit 1; }

# Vektörleri oluştur
echo "Vektörler oluşturuluyor..."
python3 src/embedder.py || { echo "Hata: Vektör oluşturma başarısız"; deactivate; exit 1; }

# Streamlit uygulamasını çalıştır
echo "Streamlit uygulaması başlatılıyor..."
streamlit run app/main.py --server.fileWatcherType none --server.port 8501 || { echo "Hata: Streamlit başlatılamadı"; deactivate; exit 1; }

# Sanal ortamı deaktive et
echo "Sanal ortam deaktive ediliyor..."
deactivate