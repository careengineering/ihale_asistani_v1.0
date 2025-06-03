import pickle
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def load_embeddings(path: str):
    import pickle
    with open(path, "rb") as f:
        embeddings, metadata = pickle.load(f)
    return embeddings, metadata



def retrieve_top_k(question_variants, embeddings, metadata, k=3):
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    question_embeddings = model.encode(question_variants, convert_to_numpy=True)
    avg_question_embedding = np.mean(question_embeddings, axis=0)

    similarities = np.dot(embeddings, avg_question_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(avg_question_embedding)
    )
    top_k_indices = np.argsort(similarities)[-k:][::-1]

    top_k_items = [metadata[i] for i in top_k_indices if similarities[i] > 0.3]  # filtreleme
    return top_k_items