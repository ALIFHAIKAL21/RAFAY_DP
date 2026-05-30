import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import REVISION_MATCH_TRAIN_DATA, TRAIN_DATA_CLEAN


DEFAULT_SOURCE = TRAIN_DATA_CLEAN
SOURCE_PATH = Path(
    os.getenv("REVISION_MATCH_SOURCE_DATA_PATH", str(DEFAULT_SOURCE))
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _detokenize_tokens(tokens: List[str]) -> List[Dict[str, str]]:
    words: List[Dict[str, str]] = []
    for tok in tokens:
        token = str(tok or "")
        if token in {"[CLS]", "[SEP]"}:
            continue

        if token.startswith("##") and words:
            words[-1]["text"] += token[2:]
            continue

        words.append({"text": token, "tag": "O"})
    return words


def _words_with_tags(tokens: List[str], ner_tags: List[str]) -> List[Dict[str, str]]:
    words: List[Dict[str, str]] = []
    for token, tag in zip(tokens, ner_tags):
        token = str(token or "")
        tag = str(tag or "O")
        if token in {"[CLS]", "[SEP]"}:
            continue

        if token.startswith("##") and words:
            words[-1]["text"] += token[2:]
            # Keep the existing BIO tag on the merged base token.
            continue

        words.append({"text": token, "tag": tag})
    return words


def _extract_entities(tokens: List[str], ner_tags: List[str]) -> Dict[str, List[str]]:
    words = _words_with_tags(tokens, ner_tags)
    entities: Dict[str, List[str]] = defaultdict(list)

    active_type: Optional[str] = None
    active_tokens: List[str] = []

    def flush():
        nonlocal active_type, active_tokens
        if active_type and active_tokens:
            value = _clean(" ".join(active_tokens))
            if value:
                entities[active_type].append(value)
        active_type = None
        active_tokens = []

    for item in words:
        text = item["text"]
        tag = item["tag"]

        if tag == "O" or "-" not in tag:
            flush()
            continue

        prefix, ent_type = tag.split("-", 1)

        if prefix == "B":
            flush()
            active_type = ent_type
            active_tokens = [text]
            continue

        if prefix == "I":
            if active_type == ent_type and active_tokens:
                active_tokens.append(text)
            else:
                # Broken BIO sequence fallback.
                flush()
                active_type = ent_type
                active_tokens = [text]
            continue

        flush()

    flush()
    return dict(entities)


def _first_non_empty(entities: Dict[str, List[str]], keys: List[str]) -> str:
    for k in keys:
        values = entities.get(k) or []
        for v in values:
            if _clean(v):
                return _clean(v)
    return ""


def _build_candidate_text(structured: Dict[str, str]) -> str:
    lines = [
        f"RO_DATE: {structured.get('ro_date') or '-'}",
        f"LOAD_DATE: {structured.get('load_date') or '-'}",
        f"TIME: {structured.get('time') or '-'}",
        f"ORIGIN: {structured.get('origin') or '-'}",
        f"DESTINATION: {structured.get('destination') or '-'}",
        f"UNIT_TYPE: {structured.get('unit_type') or '-'}",
        f"DRIVER: {structured.get('driver') or '-'}",
        f"PLATE: {structured.get('plate') or '-'}",
        f"PHONE: {structured.get('phone') or '-'}",
    ]
    return "\n".join(lines)


def _build_synthetic_revision(structured: Dict[str, str]) -> str:
    chunks = ["REQUEST ULANG ORDER ONCALL"]
    if structured.get("ro_date"):
        chunks.append(f"Tanggal: {structured['ro_date']}")
    if structured.get("origin"):
        chunks.append(f"Lokasi: {structured['origin']}")
    if structured.get("destination"):
        chunks.append(f"Rute/tujuan: {structured['destination']}")
    if structured.get("time"):
        chunks.append(f"Waktu loading: {structured['time']}")
    if structured.get("driver"):
        chunks.append(f"Driver: {structured['driver']}")
    if structured.get("plate"):
        chunks.append(f"Nopol: {structured['plate']}")
    if structured.get("phone"):
        chunks.append(f"No hp: {structured['phone']}")
    return "\n".join(chunks)


def _record_signature(structured: Dict[str, str]) -> str:
    parts = [
        structured.get("ro_date", "").upper(),
        structured.get("load_date", "").upper(),
        structured.get("time", "").upper(),
        structured.get("origin", "").upper(),
        structured.get("destination", "").upper(),
        structured.get("unit_type", "").upper(),
        structured.get("driver", "").upper(),
        structured.get("plate", "").upper(),
        structured.get("phone", "").upper(),
    ]
    return "|".join(parts)


def _route_key(structured: Dict[str, str]) -> str:
    return "|".join(
        [
            structured.get("origin", "").upper(),
            structured.get("destination", "").upper(),
            structured.get("unit_type", "").upper(),
        ]
    )


def _build_records(source_rows: List[Dict]) -> List[Dict]:
    records: List[Dict] = []
    seen_signatures = set()

    for row in source_rows:
        entities = _extract_entities(row.get("tokens", []), row.get("ner_tags", []))
        structured = {
            "ro_date": _first_non_empty(entities, ["RO_DATE"]),
            "load_date": _first_non_empty(entities, ["LOAD_DATE"]),
            "time": _first_non_empty(entities, ["TIME"]),
            "origin": _first_non_empty(entities, ["ORIGIN"]),
            "destination": _first_non_empty(entities, ["DESTINATION"]),
            "unit_type": _first_non_empty(entities, ["UNIT_TYPE"]),
            "driver": _first_non_empty(entities, ["DRIVER"]),
            "plate": _first_non_empty(entities, ["PLATE"]),
            "phone": _first_non_empty(entities, ["PHONE"]),
        }

        original_text = _clean(row.get("original_text", ""))
        if not original_text:
            # Fallback to detokenized text when original_text is missing.
            detok = [w["text"] for w in _detokenize_tokens(row.get("tokens", []))]
            original_text = _clean(" ".join(detok))

        candidate_text = _build_candidate_text(structured)
        signature = _record_signature(structured)

        # Remove exact duplicated records to avoid data leakage.
        if signature in seen_signatures and original_text == "":
            continue
        seen_signatures.add(signature)

        records.append(
            {
                "source_id": row.get("id"),
                "original_text": original_text,
                "synthetic_text": _build_synthetic_revision(structured),
                "candidate_text": candidate_text,
                "signature": signature,
                "route_key": _route_key(structured),
                "structured": structured,
            }
        )

    return records


def _pick_hard_negative(records: List[Dict], route_index: Dict[str, List[int]], idx: int) -> Optional[int]:
    rec = records[idx]
    candidates = route_index.get(rec["route_key"], [])
    filtered = [j for j in candidates if j != idx and records[j]["signature"] != rec["signature"]]
    if filtered:
        return random.choice(filtered)
    return None


def _pick_random_negative(records: List[Dict], idx: int) -> Optional[int]:
    candidates = [j for j in range(len(records)) if j != idx and records[j]["signature"] != records[idx]["signature"]]
    if not candidates:
        return None
    return random.choice(candidates)


def _build_pairs(records: List[Dict]) -> List[Dict]:
    pairs: List[Dict] = []
    route_index: Dict[str, List[int]] = defaultdict(list)
    for i, rec in enumerate(records):
        route_index[rec["route_key"]].append(i)

    for i, rec in enumerate(records):
        # Positive pair from raw text.
        if rec["original_text"]:
            pairs.append(
                {
                    "pair_id": f"{rec['source_id']}_pos_original",
                    "text_a": rec["original_text"],
                    "text_b": rec["candidate_text"],
                    "label": "MATCH",
                    "pair_kind": "positive_original",
                    "source_id": rec["source_id"],
                }
            )

        # Positive pair from synthetic revision text.
        synthetic_text = rec["synthetic_text"]
        if synthetic_text:
            pairs.append(
                {
                    "pair_id": f"{rec['source_id']}_pos_synthetic",
                    "text_a": synthetic_text,
                    "text_b": rec["candidate_text"],
                    "label": "MATCH",
                    "pair_kind": "positive_synthetic",
                    "source_id": rec["source_id"],
                }
            )

        hard_j = _pick_hard_negative(records, route_index, i)
        if hard_j is not None:
            pairs.append(
                {
                    "pair_id": f"{rec['source_id']}_neg_hard",
                    "text_a": synthetic_text or rec["original_text"],
                    "text_b": records[hard_j]["candidate_text"],
                    "label": "NO_MATCH",
                    "pair_kind": "negative_hard",
                    "source_id": rec["source_id"],
                }
            )

        rand_j = _pick_random_negative(records, i)
        if rand_j is not None:
            pairs.append(
                {
                    "pair_id": f"{rec['source_id']}_neg_random",
                    "text_a": rec["original_text"] or synthetic_text,
                    "text_b": records[rand_j]["candidate_text"],
                    "label": "NO_MATCH",
                    "pair_kind": "negative_random",
                    "source_id": rec["source_id"],
                }
            )

    # Keep only valid rows.
    return [
        p
        for p in pairs
        if _clean(p.get("text_a")) and _clean(p.get("text_b")) and _clean(p.get("label"))
    ]


def main():
    random.seed(42)
    print("Menyiapkan dataset Revision Target Matcher...")
    print(f"Input : {SOURCE_PATH}")
    print(f"Output: {REVISION_MATCH_TRAIN_DATA}")

    if not SOURCE_PATH.exists():
        print(f"ERROR: file sumber tidak ditemukan: {SOURCE_PATH}")
        return

    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        source_rows = json.load(f)

    records = _build_records(source_rows)
    pairs = _build_pairs(records)

    REVISION_MATCH_TRAIN_DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(REVISION_MATCH_TRAIN_DATA, "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)

    label_dist = Counter(p["label"] for p in pairs)
    kind_dist = Counter(p["pair_kind"] for p in pairs)

    print(f"Total source records : {len(records)}")
    print(f"Total pair samples   : {len(pairs)}")
    print(f"Label distribution   : {dict(label_dist)}")
    print(f"Pair kind distribution: {dict(kind_dist)}")
    print("Selesai.")


if __name__ == "__main__":
    main()
