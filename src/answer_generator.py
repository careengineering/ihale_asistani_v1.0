from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

def generate_answer(question: str) -> str:
    prompt = (
        "Aşağıdaki kullanıcı sorusunu, Türk ihale mevzuatına uygun şekilde, "
        "resmi ve açık bir dille cevapla.\n\n"
        f"Soru: {question}\n\nCevap:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # veya "gpt-4"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT cevabı alınamadı]: {e}"
