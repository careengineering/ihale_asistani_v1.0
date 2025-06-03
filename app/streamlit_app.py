import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from src.data_preprocessing import load_synonyms, expand_question_with_synonyms
from src.retriever import load_embeddings, retrieve_top_k
from src.answer_generator import generate_answer  # Artık sadece yorum döndürüyor

# Ayarlar
EMBEDDING_PATH = "data/embeddings/ihale_embeddings.pkl"
SYNONYM_PATH = "data/synonyms/EsAnlamlilar.csv"
TOP_K = 3

# Sayfa ayarı
st.set_page_config(page_title="İhale Mevzuat Asistanı", layout="wide")
st.title("📘 İhale Mevzuat Asistanı")
st.markdown("Sorduğunuz soruya mevzuata uygun yorumlarla cevap verir.")

# Veri yükleme
with st.spinner("Veriler yükleniyor..."):
    try:
        embeddings, metadata = load_embeddings(EMBEDDING_PATH)
        synonyms = load_synonyms(SYNONYM_PATH) if os.path.exists(SYNONYM_PATH) else {}
        model_loaded = True
    except Exception as e:
        st.error(f"Veriler yüklenirken hata oluştu: {e}")
        model_loaded = False

# Soru al ve işleme başla
if model_loaded:
    soru = st.text_input("🔎 Sorunuzu girin:", placeholder="Örn: diploma iş deneyim yerine geçer mi?")
    
    if soru:
        # Soru varyasyonları üret
        expanded = expand_question_with_synonyms(soru, synonyms)

        # En uygun mevzuat maddelerini getir
        with st.spinner("Uygun mevzuat maddeleri aranıyor..."):
            results = retrieve_top_k(expanded, embeddings, metadata, k=TOP_K)

        # Mevzuat kaynaklarını göster
        st.subheader("📄 Uygun Mevzuat Maddeleri")
        for result in results:
            st.markdown(f"### {result['mevzuat_adi']} - Madde {result['madde_no']}")
            st.markdown(result['icerik'])
            st.markdown("---")

        # Asistan yorumu
        st.subheader("🧾 Asistanın Yorumu")
        with st.spinner("Cevap hazırlanıyor..."):
            st.markdown(generate_answer(soru))
