import torch
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import EVENT_OUTPUT_DIR


class EventClassifierInference:
    def __init__(self, model_path=None):
        default_local_path = EVENT_OUTPUT_DIR / "final_model"

        if model_path is None:
            if not default_local_path.exists():
                raise FileNotFoundError(
                    f"Model event classifier tidak ditemukan: {default_local_path}"
                )
            self.model_path = str(default_local_path)
        else:
            candidate = Path(str(model_path))
            self.model_path = str(candidate) if candidate.exists() else str(model_path)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.to(self.device)
        self.model.eval()

        self.id2label = self.model.config.id2label

    def predict(self, text):
        cleaned_text = str(text or "").strip()
        if not cleaned_text:
            return {"label": "NON_ORDER", "score": 0.0}

        inputs = self.tokenizer(
            cleaned_text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
            pred_id = int(torch.argmax(probs).item())
            score = float(probs[pred_id].item())

        return {
            "label": self.id2label.get(pred_id, str(pred_id)),
            "score": score,
        }
