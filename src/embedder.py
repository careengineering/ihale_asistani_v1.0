import json
from sentence_transformers import SentenceTransformer
import faiss
import torch
import numpy as np

class Embedder:
    def __init__(self, model_name="distiluse-base-multilingual-cased-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Embedder Device: {self.device}")  # Cihazı doğrulamak için
        self.model = SentenceTransformer(model_name, device=self.device)
    
    def embed_texts(self, texts):
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=True, device=self.device, batch_size=16)
            return embeddings.cpu().numpy()
        except Exception as e:
            print(f"Hata: Metinler vektörleştirilemedi. {e}")
            raise
    
    def save_embeddings(self, texts, output_index_path="data/embeddings/mevzuat_embeddings.faiss", output_metadata_path="data/embeddings/mevzuat_metadata.json"):
        try:
            # Metinleri küçük gruplar halinde işleyerek hafıza kullanımını optimize etme
            batch_size = 500
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_embeddings = self.embed_texts(batch)
                embeddings.append(batch_embeddings)
            embeddings = np.vstack(embeddings)
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)
            faiss.write_index(index, output_index_path)
            metadata = [{"text": text} for text in texts]
            with open(output_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            print(f"Embeddings kaydedildi: {output_index_path}, Metadata kaydedildi: {output_metadata_path}")
        except Exception as e:
            print(f"Hata: Vektörleştirme başarısız. {e}")
            raise

if __name__ == "__main__":
    with open("data/processed/mevzuat_chunks.json", 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    texts = [chunk["text"] for chunk in chunks]
    embedder = Embedder()
    embedder.save_embeddings(texts)