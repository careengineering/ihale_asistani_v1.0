import pickle
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def load_embeddings(pickle_path: str) -> Tuple[np.ndarray, List[Dict]]:
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    return data["embeddings"], data["metadata"]


def retrieve_top_k(question_variants: List[str], embeddings: np.ndarray, metadata: List[Dict], k: int = 3) -> List[Dict]:
    question_embeddings = model.encode(question_variants, convert_to_numpy=True)
    avg_question_embedding = np.mean(question_embeddings, axis=0)

    similarities = np.dot(embeddings, avg_question_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(avg_question_embedding) + 1e-10
    )
    top_k_indices = np.argsort(similarities)[-k:][::-1]

    results = []
    for idx in top_k_indices:
        entry = metadata[idx].copy()
        entry["similarity"] = float(similarities[idx])
        results.append(entry)

    return results