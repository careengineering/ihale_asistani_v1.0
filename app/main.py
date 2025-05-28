from data_preprocessing import load_synonyms, expand_question_with_synonyms
from retriever import load_embeddings, retrieve_top_k
from model import generate_answer
import os

EMBEDDING_PATH = "data/embeddings/ihale_embeddings.pkl"
SYNONYM_PATH = "data/EsAnlamlilar.csv"


def soru_sor(soru: str):
    if not os.path.exists(EMBEDDING_PATH):
        print("[HATA] Embedding dosyası bulunamadı. Lütfen önce embedder.py çalıştırarak vektörleri oluşturun.")
        return

    print("[INFO] Veriler yükleniyor...")
    embeddings, metadata = load_embeddings(EMBEDDING_PATH)
    synonyms = load_synonyms(SYNONYM_PATH)
    expanded_questions = expand_question_with_synonyms(soru, synonyms)

    print("[INFO] En benzer mevzuat maddeleri aranıyor...")
    results = retrieve_top_k(expanded_questions, embeddings, metadata, k=3)

    print("[INFO] Yanıt oluşturuluyor...")
    cevap = generate_answer(results, soru)
    print(cevap)


if __name__ == "__main__":
    while True:
        user_input = input("\n🔍 Sorunuzu girin (çıkmak için 'q'): ")
        if user_input.lower() == 'q':
            break
        soru_sor(user_input)