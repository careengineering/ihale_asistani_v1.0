import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from src.data_preprocessing import load_synonyms, expand_question_with_synonyms
from src.retriever import load_embeddings, retrieve_top_k
from src.model import generate_answer
import os

st.set_page_config(page_title="İhale Asistanı", layout="wide")

st.title("📘 İhale Asistanı")
st.markdown("""
İhale Asistanı, kullanıcıların ihale süreçlerine ilişkin sorularına ilgili mevzuat maddelerini bularak yanıt veren bir yapay zeka asistanıdır. Bu araç herkese açık verilerden ve ücretsiz modellerden faydalanır.

🔔 **Uyarı:** Bu sistem hukuki danışmanlık amacı taşımaz. Verilen cevaplar mevzuatın öne çıkan maddelerine dayansa da nihai kararlar için resmi kaynaklar ve uzman görüşü esas alınmalıdır.
""")

EMBEDDING_PATH = "data/embeddings/ihale_embeddings.pkl"
SYNONYM_PATH = "data/EsAnlamlilar.csv"

st.sidebar.header("Ayarlar")
ihale_turu = st.sidebar.selectbox("İhale Türü", ["Genel", "Mal", "Hizmet", "Yapım", "Danışmanlık"])

soru = st.text_input("💬 Sorunuzu yazınız:", placeholder="Örn: diploma iş deneyim yerine geçer mi?")

if st.button("🚀 Sorgula") and soru:
    if not os.path.exists(EMBEDDING_PATH):
        st.error("Embedding dosyası bulunamadı. Lütfen sistem yöneticisine başvurun.")
    else:
        with st.spinner("Veriler yükleniyor..."):
            embeddings, metadata = load_embeddings(EMBEDDING_PATH)
            synonyms = load_synonyms(SYNONYM_PATH)
            expanded = expand_question_with_synonyms(soru, synonyms)

        with st.spinner("En uygun mevzuat maddeleri aranıyor..."):
            results = retrieve_top_k(expanded, embeddings, metadata, k=3)

        with st.spinner("Cevap oluşturuluyor..."):
            cevap = generate_answer(results, soru)

        st.markdown("---")
        st.markdown(f"### 📄 Soru: `{soru}`")
        st.markdown(cevap)

        puan = st.radio("Bu cevabı nasıl puanlarsınız?", [1, 2, 3, 4, 5], horizontal=True)
        st.success(f"Teşekkürler! {puan} puan verdiniz.")

