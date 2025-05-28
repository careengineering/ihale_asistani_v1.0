import os
import json
import pickle
from typing import List, Dict
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def generate_embeddings_from_processed(processed_dir: str, output_path: str):
    corpus = []
    metadata = []

    for filename in os.listdir(processed_dir):
        if filename.endswith(".json"):
            with open(os.path.join(processed_dir, filename), "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    corpus.append(item["icerik"])
                    metadata.append({
                        "mevzuat_adi": item["mevzuat_adi"],
                        "madde_no": item["madde_no"],
                        "icerik": item["icerik"]
                    })

    print(f"[INFO] Embedding {len(corpus)} segments...")
    embeddings = model.encode(corpus, show_progress_bar=True, convert_to_numpy=True)

    with open(output_path, "wb") as f:
        pickle.dump({"embeddings": embeddings, "metadata": metadata}, f)

    print(f"[INFO] Embeddings saved to {output_path}")
