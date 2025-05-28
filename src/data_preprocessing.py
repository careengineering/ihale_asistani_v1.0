import os
import re
import pandas as pd
from typing import List, Dict


def load_synonyms(file_path: str) -> Dict[str, List[str]]:
    df = pd.read_csv(file_path)
    synonyms = {}
    for _, row in df.iterrows():
        values = [v.strip().lower() for v in row.dropna().values if isinstance(v, str)]
        for word in values:
            synonyms[word] = list(set(values) - {word})
    return synonyms

def expand_question_with_synonyms(question: str, synonyms: Dict[str, List[str]]) -> List[str]:
    words = question.lower().split()
    expanded = set([question.lower()])
    for i, word in enumerate(words):
        if word in synonyms:
            for syn in synonyms[word]:
                new_words = words[:i] + [syn] + words[i+1:]
                expanded.add(' '.join(new_words))
    return list(expanded)

def segment_law_text(content: str, mevzuat_adi: str) -> List[Dict]:
    madde_pattern = re.compile(r"(Madde\\s+\\d+[A-Za-z\\d]*)(?=[\\s\\-:])", re.IGNORECASE)
    matches = list(madde_pattern.finditer(content))
    segments = []
    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        madde_no = matches[i].group().strip().replace(':', '').replace('Madde', '').strip()
        icerik = content[start:end].strip()
        segments.append({
            "mevzuat_adi": mevzuat_adi,
            "madde_no": madde_no,
            "icerik": icerik
        })
    return segments


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def preprocess_raw_mevzuat(raw_dir: str, output_dir: str):
    import json
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(raw_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(raw_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            mevzuat_adi = filename.replace(".txt", "")
            segments = segment_law_text(content, mevzuat_adi)
            cleaned_segments = [{**seg, "icerik": clean_text(seg["icerik"])} for seg in segments if len(seg["icerik"]) > 30]

            with open(os.path.join(output_dir, mevzuat_adi + ".json"), "w", encoding="utf-8") as f:
                json.dump(cleaned_segments, f, ensure_ascii=False, indent=2)

    print("[INFO] Preprocessing completed.")
