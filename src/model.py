from typing import List, Dict

def generate_answer(retrieved_docs: List[Dict], user_question: str) -> str:
    response = []

    response.append("\nSoru: " + user_question)
    response.append("\n\nİlgili Mevzuat Maddeleri:\n")

    for doc in retrieved_docs:
        mevzuat = doc.get("mevzuat_adi", "")
        madde = doc.get("madde_no", "")
        icerik = doc.get("icerik", "")
        sim = doc.get("similarity", 0)

        response.append(f"📘 {mevzuat} - Madde {madde} (Benzerlik: {sim:.2f})\n{icerik}\n")

    response.append("\n📌 Açıklama:\n")
    response.append("Yukarıda belirtilen mevzuatlara göre, sorunuzla ilişkili olan maddeler yukarıda listelenmiştir. Bu maddeler çerçevesinde değerlendirme yapılabilir.")

    response.append("\n\nLütfen aşağıdaki şekilde puanlama yapınız (1-5):")
    response.append("\n1 - İlgisiz | 2 - Kısmen Alakalı | 3 - Orta | 4 - İyi | 5 - Çok İyi")

    return "\n".join(response)