import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import EVENT_RAW_LABEL_STUDIO, EVENT_TRAIN_DATA


CANONICAL_LABELS = ("NEW_ORDER", "UPDATE", "NON_ORDER")


def normalize_event_label(raw_label):
    if not raw_label:
        return None

    label = str(raw_label).strip().upper()

    if label in {"NEW_ORDER", "NEW", "ORDER_BARU"}:
        return "NEW_ORDER"
    if label in {"UPDATE", "REVISI", "GANTI", "UBAH"}:
        return "UPDATE"
    if label in {"NON_ORDER", "CANCEL", "INFO", "OTHER"}:
        return "NON_ORDER"
    return None


def extract_choice_label(task):
    sources = []

    annotations = task.get("annotations") or []
    if isinstance(annotations, list):
        sources.extend(annotations)

    predictions = task.get("predictions") or []
    if isinstance(predictions, list):
        sources.extend([p for p in predictions if isinstance(p, dict)])

    for source in sources:
        result = source.get("result") or []
        for item in result:
            if item.get("type") != "choices":
                continue
            choices = item.get("value", {}).get("choices") or []
            if choices:
                label = normalize_event_label(choices[0])
                if label:
                    return label

    return None


def fallback_label_from_text(text):
    txt = str(text or "").lower()
    if not txt:
        return None

    if re.search(r"\b(revisi|update|ubah|ganti)\b", txt):
        return "UPDATE"
    if re.search(r"\b(cancel|batal|info|fyi)\b", txt):
        return "NON_ORDER"
    if re.search(r"\b(request|order|oncall|unit)\b", txt):
        return "NEW_ORDER"
    return None


def main():
    print("Menyiapkan dataset event classifier...")
    print(f"Input : {EVENT_RAW_LABEL_STUDIO}")
    print(f"Output: {EVENT_TRAIN_DATA}")

    if not EVENT_RAW_LABEL_STUDIO.exists():
        print(f"ERROR: file tidak ditemukan: {EVENT_RAW_LABEL_STUDIO}")
        return

    with open(EVENT_RAW_LABEL_STUDIO, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    rows = []
    for task in tasks:
        text = str(task.get("data", {}).get("text", "")).strip()
        if not text:
            continue

        label = extract_choice_label(task)
        if label is None:
            label = fallback_label_from_text(text)
        if label is None:
            continue

        rows.append(
            {
                "id": task.get("id"),
                "text": text,
                "label": label,
            }
        )

    EVENT_TRAIN_DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENT_TRAIN_DATA, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    dist = Counter(r["label"] for r in rows)
    print(f"Total data: {len(rows)}")
    print(f"Distribusi: {dict(dist)}")
    missing = [l for l in CANONICAL_LABELS if l not in dist]
    if missing:
        print(f"Catatan: label berikut belum ada di data: {missing}")
    print("Selesai.")


if __name__ == "__main__":
    main()
