import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import torch
import pandas as pd

class Retriever:
    def __init__(self, index_path, metadata_path, model_name="distiluse-base-multilingual-cased-v2", synonym_file="data/EsAnlamlilar.csv"):
        self.model = SentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Retriever Device: {self.device}")  # Cihazı doğrulamak için
        self.index = faiss.read_index(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        faiss.omp_set_num_threads(4)

        # Eşanlamlılar dosyasını yükle
        self.synonym_dict = self.load_synonyms(synonym_file)

    def load_synonyms(self, synonym_file):
        """Eşanlamlılar dosyasını okur ve bir sözlük oluşturur."""
        try:
            df = pd.read_csv(synonym_file, encoding='utf-8')
            synonym_dict = {}
            for _, row in df.iterrows():
                word = row['Kelime'].strip().lower()
                synonyms = [syn.strip().lower() for syn in row['Eşanlamlılar'].split(',')]
                synonym_dict[word] = synonyms
                # Her eşanlamlıyı da ana kelimeye bağla (çift yönlü eşleşme)
                for syn in synonyms:
                    if syn not in synonym_dict:
                        synonym_dict[syn] = [word] + [s for s in synonyms if s != syn]
            print(f"Eşanlamlılar yüklendi: {len(synonym_dict)} kelime.")
            return synonym_dict
        except Exception as e:
            print(f"Hata: Eşanlamlılar dosyası yüklenemedi. {e}")
            return {}

    def expand_query(self, query):
        """Sorgudaki kelimeleri eşanlamlılarıyla genişletir."""
        words = query.lower().split()
        expanded_words = []
        for word in words:
            if word in self.synonym_dict:
                expanded_words.extend(self.synonym_dict[word])
            expanded_words.append(word)
        expanded_query = " ".join(set(expanded_words))  # Tekrarları kaldır
        print(f"Genişletilmiş sorgu: {expanded_query}")
        return expanded_query

    def clean_text(self, text):
        text = re.sub(r'[^\w\s.,;:-çğışöüÇĞİŞÖÜ]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def retrieve(self, query, top_k=5, max_distance=0.7, ihale_type="Genel"):
        try:
            # Sorguyu eşanlamlılarla genişlet
            expanded_query = self.expand_query(query)
            query_embedding = self.model.encode([self.clean_text(expanded_query)], convert_to_tensor=False)
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