from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import List, Dict

# Use google/mt5-small for Turkish text generation
tokenizer = AutoTokenizer.from_pretrained("google/mt5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("google/mt5-small")

def generate_answer(question: str, retrieved_docs: List[Dict]) -> str:
    # Construct a prompt that includes the question and relevant document excerpts
    prompt = f"Soru: {question}\n\nİlgili Mevzuat:\n"
    for doc in retrieved_docs:
        mevzuat = doc.get("mevzuat_adi", "Bilinmiyor")
        madde = doc.get("madde_no", "—")
        icerik = doc.get("icerik", "")[:500]  # Limit content length to avoid token overflow
        prompt += f"{mevzuat} - Madde {madde}:\n{icerik}\n\n"
    prompt += "Yukarıdaki mevzuat bilgilerine dayanarak soruya yanıt ver ve bir açıklama yap."

    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            top_p=0.9
        )
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return answer
    except Exception as e:
        return f"[Yorum üretilemedi]: {e}"