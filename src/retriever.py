import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import re

class Retriever:
    def __init__(self, index_path, metadata_path, model_name="distiluse-base-multilingual-cased-v2"):
        self.model = SentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")
        self.index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        faiss.omp_set_num_threads(4)

    def clean_text(self, text):
        text = re.sub(r'[^\w\s.,;:-çğışöüÇĞİŞÖÜ]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def retrieve(self, query, top_k=5, max_distance=0.7, ihale_type="Genel"):
        try:
            query_embedding = self.model.encode([self.clean_text(query)], convert_to_tensor=False)
            distances, indices = self.index.search(query_embedding, top_k)
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if distance > max_distance:
                    continue
                metadata = self.metadata[idx]
                if ihale_type != "Genel" and metadata.get("ihale_type") != ihale_type:
                    continue
                results.append({
                    "text": self.clean_text(metadata["text"]),
                    "mevzuat_name": metadata["mevzuat_name"],
                    "distance": float(distance),
                    "ihale_type": metadata.get("ihale_type", "Genel"),
                    "kik_date": metadata.get("kik_date"),
                    "kik_number": metadata.get("kik_number")
                })
            return results[:top_k]
        except Exception as e:
            print(f"Hata: Arama yapılamadı. {e}")
            return []