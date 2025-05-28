import torch
from transformers import pipeline

class ResponseGenerator:
    def __init__(self, model_name="savasy/bert-base-turkish-squad"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.qa_pipeline = pipeline(
            "question-answering",
            model=model_name,
            tokenizer=model_name,
            device=0 if self.device.type == "cuda" else -1
        )

    def generate_answer(self, question, context, max_context_length=512):
        try:
            context = context[:max_context_length]
            result = self.qa_pipeline({
                "question": question,
                "context": context
            })
            answer = result["answer"].strip()
            if not answer or len(answer) < 3:
                return "Üzgünüz, soruya uygun bir cevap bulunamadı."
            return f"{answer.capitalize()}."
        except Exception as e:
            print(f"Hata: Cevap üretilemedi. {e}")
            return "Üzgünüz, soruya uygun bir cevap üretilemedi."