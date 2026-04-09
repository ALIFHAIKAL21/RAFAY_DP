from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import REVISION_MATCH_OUTPUT_DIR


class RevisionMatcherInference:
    def __init__(self, model_path=None):
        default_local_path = REVISION_MATCH_OUTPUT_DIR / "final_model"

        if model_path is None:
            if not default_local_path.exists():
                raise FileNotFoundError(
                    f"Model revision matcher tidak ditemukan: {default_local_path}"
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
        self.label2id = self.model.config.label2id
        self.match_id = self.label2id.get("MATCH", 1)

    def score_pair(self, incoming_text: str, candidate_text: str) -> Dict:
        left = str(incoming_text or "").strip()
        right = str(candidate_text or "").strip()

        if not left or not right:
            return {
                "label": "NO_MATCH",
                "score": 0.0,
                "match_probability": 0.0,
            }

        inputs = self.tokenizer(
            left,
            right,
            return_tensors="pt",
            truncation=True,
            max_length=256,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
            pred_id = int(torch.argmax(probs).item())
            pred_score = float(probs[pred_id].item())
            match_prob = float(probs[self.match_id].item())

        return {
            "label": self.id2label.get(pred_id, str(pred_id)),
            "score": pred_score,
            "match_probability": match_prob,
        }

    def rank_candidates(
        self, incoming_text: str, candidates: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        ranked = []
        for item in candidates:
            candidate_text = str(item.get("candidate_text", "")).strip()
            if not candidate_text:
                continue
            score = self.score_pair(incoming_text, candidate_text)
            ranked.append(
                {
                    **item,
                    "predicted_label": score["label"],
                    "match_probability": score["match_probability"],
                }
            )

        ranked.sort(key=lambda x: x["match_probability"], reverse=True)
        return ranked[: max(1, int(top_k))]
