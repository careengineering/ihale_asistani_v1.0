import streamlit as st
import sys
import os

# src dizinini Python yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retriever import Retriever
from src.model import ResponseGenerator

# Streamlit sayfa yapılandırması
st.set_page_config(page_title="İhale Asistanı", layout="wide")

# CSS ile arayüzü düzenleme
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #4CAF50; color: white; }
    .stTextInput>div>input { border-radius: 5px; }
    h1 { color: #2E7D32; }
</style>
""", unsafe_allow_html=True)

# Modelleri başlatma
@st.cache_resource
def initialize_models():
    retriever = Retriever(
        index_path="data/embeddings/mevzuat_embeddings.faiss",
        metadata_path="data/embeddings/mevzuat_metadata.json",
        model_name="distiluse-base-multilingual-cased-v2",
        synonym_file="data/EsAnlamlilar.csv"
    )
    generator = ResponseGenerator(model_name="savasy/bert-base-turkish-squad")
    return retriever, generator

st.title("İhale Asistanı")
st.markdown("İhale süreçleriyle ilgili sorularınızı yanıtlayan bir asistan.")

# Model yükleme
with st.spinner("Modeller yükleniyor..."):
    retriever, generator = initialize_models()

# Sekmeler
tab1, tab2 = st.tabs(["Soru Sor", "Geçmiş Etkileşimler"])

# Soru sorma sekmesi
with tab1:
    st.subheader("Soru Sor")
    st.write("İhale türünü seçerek sorunuzun daha iyi filtrelenmesini sağlayabilirsiniz.")

    # Form ile soru girişi
    with st.form(key="question_form"):
        ihale_type = st.selectbox(
            "İhale türünü seçin:",
            ["Genel", "Mal", "Hizmet", "Yapım", "Danışmanlık"]
        )
        query = st.text_input(
            "İhale ile ilgili sorunuzu girin (örn: 'Diploma iş deneyim belgesi yerine geçer mi?'):",
            key="query_input"
        )
        submit_button = st.form_submit_button(label="Soruyu Gönder")

        if submit_button or query:
            if query.strip() == "":
                st.warning("Lütfen bir soru girin.")
            else:
                with st.spinner("Sorgunuz işleniyor..."):
                    # Retriever ile ilgili metinleri al
                    results = retriever.retrieve(query, top_k=5, max_distance=0.7, ihale_type=ihale_type)
                    
                    if not results:
                        st.error("Üzgünüz, sorunuzla ilgili yeterli bilgi bulunamadı.")
                    else:
                        # ResponseGenerator ile cevap üret
                        context = "\n".join([res["text"] for res in results])
                        answer = generator.generate_answer(query, context)
                        
                        # Cevabı ve kaynakları göster
                        st.subheader("Mevzuat Tabanlı Yanıt")
                        st.write(f"**Yanıt:** {answer}")
                        
                        st.subheader("Kaynak Mevzuat Maddeleri")
                        for res in results:
                            st.write(f"- **{res['mevzuat_name']}** (Mesafe: {res['distance']:.4f})")
                            if "kik_date" in res and "kik_number" in res:
                                st.write(f"  - Karar No: {res['kik_number']}, Tarih: {res['kik_date']}")
                            st.write(f"  - Metin: {res['text'][:200]}...")
                        
                        # Geçmişi kaydet
                        if "history" not in st.session_state:
                            st.session_state.history = []
                        st.session_state.history.append({
                            "question": query,
                            "answer": answer,
                            "ihale_type": ihale_type,
                            "sources": results
                        })

# Geçmiş etkileşimler sekmesi
with tab2:
    st.subheader("Geçmiş Etkileşimler")
    if "history" not in st.session_state or not st.session_state.history:
        st.write("Henüz kaydedilmiş etkileşim yok.")
    else:
        for i, entry in enumerate(st.session_state.history):
            st.write(f"**Soru {i+1}:** {entry['question']}")
            st.write(f"**İhale Türü:** {entry['ihale_type']}")
            st.write(f"**Yanıt:** {entry['answer']}")
            st.write("**Kaynaklar:**")
            for src in entry["sources"]:
                st.write(f"- {src['mevzuat_name']} (Mesafe: {src['distance']:.4f})")
            st.write("---")