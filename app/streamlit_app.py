import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from src.data_preprocessing import load_synonyms, expand_question_with_synonyms
from src.retriever import load_embeddings, retrieve_top_k
from src.answer_generator import generate_answer

# Başlık ve tanıtım
st.set_page_config(page_title="📘 İhale Mevzuat Asistanı", layout="wide")
st.title("📘 İhale Mevzuat Asistanı")
st.markdown("Sorduğunuz soruya mevzuata uygun yorumlarla cevap verir.\n")

# 🔄 Verileri yükle
EMBEDDING_PATH = "data/embeddings/ihale_embeddings.pkl"
SYNONYM_PATH = "data/EsAnlamlilar.csv"

try:
    embeddings, metadata = load_embeddings(EMBEDDING_PATH)
    synonyms = load_synonyms(SYNONYM_PATH)
except Exception as e:
    st.error(f"Veriler yüklenirken hata oluştu: {e}")
    st.stop()

# 🔍 Soru girişi
soru = st.text_input("🔎 Sorunuzu girin:")

if soru:
    expanded = expand_question_with_synonyms(soru, synonyms)

    with st.spinner("En uygun mevzuat maddeleri aranıyor..."):
        results = retrieve_top_k(expanded, embeddings, metadata, k=3)

    if not results:
        st.warning("Soruya uygun mevzuat maddesi bulunamadı.")
    else:
        st.subheader("📄 Uygun Mevzuat Maddeleri")
        for result in results:
            mevzuat_adi = result.get("mevzuat_adi", "Bilinmiyor")
            madde_no = result.get("madde_no", "—")
            icerik = result.get("icerik", "İçerik bulunamadı.")

            st.markdown(f"**{mevzuat_adi}** — Madde {madde_no}")
            st.markdown(icerik)
            st.markdown("---")

    with st.spinner("🧠 Asistan yorumunu oluşturuyor..."):
        yorum = generate_answer(soru)

    st.subheader("🧾 Asistanın Yorumu")
    st.markdown(yorum)
