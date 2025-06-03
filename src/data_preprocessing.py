import os
import re
import json
import fitz  # PyMuPDF
import docx
from bs4 import BeautifulSoup
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

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".html":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")
            return soup.get_text()
    return ""


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])


def segment_law_text(content: str, mevzuat_adi: str) -> List[Dict]:
    madde_pattern = re.compile(r"(Madde\s+\d+[A-Za-z\d]*)[:\s]+", re.IGNORECASE)
    matches = list(madde_pattern.finditer(content))
    segments = []

    if not matches:
        madde_no = "Genel"
        if "karar no" in content.lower():
            madde_no = "Kurul Kararı"
        return [{
            "mevzuat_adi": mevzuat_adi,
            "madde_no": madde_no,
            "icerik": content.strip()
        }]

    for i in range(len(matches)):
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        madde_no = matches[i].group().strip().replace("Madde", "").strip(": ").strip()
        icerik = content[start:end].strip()
        if len(icerik) > 30:
            segments.append({
                "mevzuat_adi": mevzuat_adi,
                "madde_no": madde_no,
                "icerik": icerik
            })
    return segments


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def preprocess_raw_mevzuat(raw_dir: str, output_dir: str, log_path="data/logs/preprocess_log.xlsx"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    log_data = []

    for root, _, files in os.walk(raw_dir):
        for filename in files:
            path = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".pdf", ".docx", ".txt", ".html"]:
                continue

            base_name = os.path.basename(filename)
            mevzuat_adi = (
                base_name.replace(".pdf", "")
                .replace(".docx", "")
                .replace(".txt", "")
                .replace(".html", "")
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )

            try:
                content = extract_text_from_file(path)
                if not content or len(content) < 100:
                    log_data.append({"Dosya": filename, "Mevzuat Adı": mevzuat_adi, "Madde Sayısı": 0, "Durum": "Başarısız", "Gerekçe": "İçerik çok kısa"})
                    continue

                segments = segment_law_text(content, mevzuat_adi)
                cleaned = [{**s, "icerik": clean_text(s["icerik"])} for s in segments]

                if cleaned:
                    with open(os.path.join(output_dir, f"{mevzuat_adi}.json"), "w", encoding="utf-8") as f:
                        json.dump(cleaned, f, ensure_ascii=False, indent=2)
                    log_data.append({"Dosya": filename, "Mevzuat Adı": mevzuat_adi, "Madde Sayısı": len(cleaned), "Durum": "Başarılı", "Gerekçe": ""})
                else:
                    log_data.append({"Dosya": filename, "Mevzuat Adı": mevzuat_adi, "Madde Sayısı": 0, "Durum": "Başarısız", "Gerekçe": "Hiç madde bulunamadı"})

            except Exception as e:
                log_data.append({"Dosya": filename, "Mevzuat Adı": mevzuat_adi, "Madde Sayısı": 0, "Durum": "Hata", "Gerekçe": str(e)})

    df = pd.DataFrame(log_data)
    df.to_excel(log_path, index=False)
    print(f"[✅] Ön işleme tamamlandı. Log: {log_path}")
