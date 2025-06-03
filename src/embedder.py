import os
import json
import pickle
from typing import List, Dict
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def generate_embeddings_from_processed(processed_dir: str, output_path: str):
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import pickle

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    corpus = []
    metadata = []

    for filename in os.listdir(processed_dir):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(processed_dir, filename), "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                if not all(k in item for k in ("mevzuat_adi", "madde_no", "icerik")):
                    continue  # KİK kararlarını atla
                corpus.append(item["icerik"])
                metadata.append({
                    "mevzuat_adi": item["mevzuat_adi"],
                    "madde_no": item["madde_no"],
                    "icerik": item["icerik"]
                })


    print(f"[INFO] Embedding {len(corpus)} segments...")
    embeddings = model.encode(corpus, show_progress_bar=True)

    with open(output_path, "wb") as f:
        pickle.dump((embeddings, metadata), f)

    print(f"[INFO] Embeddings saved to {output_path}")

