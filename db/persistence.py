import hashlib
import json
import re
import uuid
from typing import Dict, Iterable, List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from db.database import SessionLocal
from models.order_dataset import OrderDataset
from models.raw_chat import RawChat
from models.stage2_match_audit import Stage2MatchAudit


_MONTH_MAP = {
    "JAN": 1,
    "JANUARI": 1,
    "JANUARY": 1,
    "FEB": 2,
    "FEBRUARI": 2,
    "FEBUARI": 2,
    "FEBRUARY": 2,
    "MAR": 3,
    "MARET": 3,
    "MARCH": 3,
    "APR": 4,
    "APRIL": 4,
    "MEI": 5,
    "MAY": 5,
    "JUN": 6,
    "JUNI": 6,
    "JUNE": 6,
    "JUL": 7,
    "JULI": 7,
    "JULY": 7,
    "AGS": 8,
    "AGU": 8,
    "AGUSTUS": 8,
    "AUG": 8,
    "AUGUST": 8,
    "SEP": 9,
    "SEPT": 9,
    "SEPTEMBER": 9,
    "OKT": 10,
    "OKTOBER": 10,
    "OCT": 10,
    "OCTOBER": 10,
    "NOV": 11,
    "NOVEMBER": 11,
    "DES": 12,
    "DESEMBER": 12,
    "DEC": 12,
    "DECEMBER": 12,
}

_MONTH_FULL_NAMES = {
    1: "JANUARI",
    2: "FEBRUARI",
    3: "MARET",
    4: "APRIL",
    5: "MEI",
    6: "JUNI",
    7: "JULI",
    8: "AGUSTUS",
    9: "SEPTEMBER",
    10: "OKTOBER",
    11: "NOVEMBER",
    12: "DESEMBER",
}


def _canonical_month_token(token: str) -> str:
    text = re.sub(r"[^A-Z]", "", _clean(token).upper())
    text = re.sub(r"([A-Z])\1+", r"\1", text)
    return text.replace("FEBUARY", "FEBRUARI").replace("FEBUARI", "FEBRUARI")


def _month_id_from_token(token: str) -> int:
    return int(_MONTH_MAP.get(_canonical_month_token(token), 0) or 0)


def _normalize_dates_for_key(value: str) -> str:
    source = _clean(value)

    def word_repl(match: re.Match) -> str:
        day = int(match.group(1))
        month = _month_id_from_token(match.group(2))
        if not month:
            return match.group(0)
        year = int(match.group(3))
        if year < 100:
            year += 2000
        return f"{day:02d} {_MONTH_FULL_NAMES[month]} {year:04d}"

    def numeric_repl(match: re.Match) -> str:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return match.group(0)
        if year < 100:
            year += 2000
        return f"{day:02d} {_MONTH_FULL_NAMES[month]} {year:04d}"

    text = re.sub(
        r"\b(\d{1,2})[\s./-]+([A-Za-z]{3,15})[\s./-]+(\d{2,4})\b",
        word_repl,
        source,
    )
    return re.sub(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        numeric_repl,
        text,
    )

_REVISION_KEYWORDS_PATTERN = re.compile(
    r"\b(rev|revisi|revision|update|ubah|ganti|perbaikan)\b",
    re.IGNORECASE,
)
_REVISION_MARKER_LINE_PATTERN = re.compile(r"(?i)^\s*(?:rev|revisi|update|ubah|ganti)\b")


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _json_dump(value) -> str:
    if value in (None, ""):
        return ""
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return ""


def _json_load(value) -> List[Dict]:
    text = _clean(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _is_blank(value) -> bool:
    txt = _clean(value).lower()
    return txt in {"", "-", "null", "none", "nan", "undefined"}


def _norm_text(value) -> str:
    txt = _clean(value).upper()
    return re.sub(r"[^A-Z0-9]+", "", txt)


def _norm_plate(value) -> str:
    return _norm_text(value)


def _norm_phone(value) -> str:
    digits = re.sub(r"\D+", "", _clean(value))
    if not digits:
        return ""
    if digits.startswith("620"):
        digits = "0" + digits[3:]
    elif digits.startswith("62"):
        digits = "0" + digits[2:]
    elif digits.startswith("8"):
        digits = "0" + digits
    return digits


def _norm_date_text(value) -> str:
    text = _normalize_dates_for_key(_clean(value)).upper()
    if not text:
        return ""

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year_token = m.group(3) or ""
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return _norm_text(value)
        if year_token:
            year = int(year_token)
            if year < 100:
                year += 2000
            return f"{day:02d}{month:02d}{year:04d}"
        return f"{day:02d}{month:02d}"

    m = re.search(r"\b(\d{1,2})\s+([A-Z]+)(?:\s+(\d{2,4}))?\b", text)
    if m:
        day = int(m.group(1))
        month = _month_id_from_token(m.group(2))
        year_token = m.group(3) or ""
        if not (1 <= day <= 31 and month):
            return _norm_text(value)
        if year_token:
            year = int(year_token)
            if year < 100:
                year += 2000
            return f"{day:02d}{month:02d}{year:04d}"
        return f"{day:02d}{month:02d}"

    return _norm_text(value)


def _row_core_filled_count(norm_row: Dict) -> int:
    fields = [
        "tgl_ro",
        "tgl_muat",
        "pickup",
        "tujuan",
        "no_plat",
        "type_truck",
        "driver",
        "kontak_driver",
    ]
    return sum(1 for f in fields if not _is_blank(norm_row.get(f)))


def _derive_status(norm_row: Dict) -> str:
    filled = _row_core_filled_count(norm_row)
    if filled >= 8:
        return "ASSIGNED"
    if filled >= 3:
        return "PARTIAL"
    return "UNASSIGNED"


def _normalize_status(value: str) -> str:
    txt = _clean(value).upper()
    if txt in {"ASSIGNED", "PARTIAL", "UNASSIGNED"}:
        return txt
    return ""


def _dataset_to_norm_row(row: OrderDataset) -> Dict:
    return {
        "job_number": _clean(row.job_number),
        "tgl_ro": _clean(row.tgl_ro),
        "tgl_muat": _clean(row.tgl_muat),
        "pickup": _clean(row.pickup),
        "tujuan": _clean(row.tujuan),
        "no_plat": _clean(row.no_plat),
        "type_truck": _clean(row.type_truck),
        "driver": _clean(row.driver),
        "kontak_driver": _clean(row.kontak_driver),
        "status_unit": _clean(row.status_unit),
    }


def _row_context_score(existing_row: OrderDataset, incoming_norm: Dict) -> int:
    score = 0
    existing_norm = _dataset_to_norm_row(existing_row)

    if not _is_blank(existing_norm["tgl_muat"]) and not _is_blank(incoming_norm["tgl_muat"]):
        score += 3 if _norm_date_text(existing_norm["tgl_muat"]) == _norm_date_text(incoming_norm["tgl_muat"]) else -3

    if not _is_blank(existing_norm["tgl_ro"]) and not _is_blank(incoming_norm["tgl_ro"]):
        score += 2 if _norm_date_text(existing_norm["tgl_ro"]) == _norm_date_text(incoming_norm["tgl_ro"]) else -2

    if not _is_blank(existing_norm["pickup"]) and not _is_blank(incoming_norm["pickup"]):
        score += 2 if _norm_text(existing_norm["pickup"]) == _norm_text(incoming_norm["pickup"]) else -3

    if not _is_blank(existing_norm["tujuan"]) and not _is_blank(incoming_norm["tujuan"]):
        score += 2 if _norm_text(existing_norm["tujuan"]) == _norm_text(incoming_norm["tujuan"]) else -3

    if not _is_blank(existing_norm["type_truck"]) and not _is_blank(incoming_norm["type_truck"]):
        score += 1 if _norm_text(existing_norm["type_truck"]) == _norm_text(incoming_norm["type_truck"]) else -2

    return score


def _looks_like_revision(chat_text: str) -> bool:
    txt = _clean(chat_text)
    if not txt:
        return False
    return bool(_REVISION_KEYWORDS_PATTERN.search(txt))


def _has_explicit_revision_marker(text: str) -> bool:
    txt = _clean(text)
    if not txt:
        return False

    for line in txt.splitlines():
        if _REVISION_MARKER_LINE_PATTERN.search(line):
            return True

    for line in txt.splitlines():
        if not _REVISION_KEYWORDS_PATTERN.search(line):
            continue
        if re.search(
            r"(?i)\b(?:driver|pengemudi|nopol|plat|no\.?\s*hp|hp|kontak|jam|waktu)\b",
            line,
        ):
            return True
    return False


def _extract_revision_old_anchors(chat_text: str) -> Dict[str, str]:
    anchors: Dict[str, str] = {}
    for line in _clean(chat_text).splitlines():
        if not _has_explicit_revision_marker(line):
            continue

        if re.search(r"(?i)\b(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\b", line):
            plate_match = re.search(r"\b([A-Z]{1,2}\s*\d{1,5}\s*[A-Z]{1,4})\b", line, re.IGNORECASE)
            if plate_match:
                plate = _norm_plate(plate_match.group(1))
                if plate:
                    anchors["no_plat"] = plate

        if re.search(r"(?i)\b(?:no\.?\s*hp|hp|no\.?\s*telp|no\.?\s*tlp|kontak)\b", line):
            phone_match = re.search(r"([+0-9][0-9\s\-]{6,})", line)
            if phone_match:
                phone = _norm_phone(phone_match.group(1))
                if phone:
                    anchors["kontak_driver"] = phone

    return anchors


def _loading_segments_from_chat(chat_text: str) -> List[str]:
    text = _clean(chat_text).replace("\r", "")
    if not text:
        return []

    loading_matches = list(re.finditer(r"(?im)^\s*Waktu\s*loading\s*:", text))
    if not loading_matches:
        return []

    starts = []
    loading_positions = [m.start() for m in loading_matches]
    for idx, start in enumerate(loading_positions):
        segment_start = start
        prefix_start = loading_positions[idx - 1] if idx > 0 else 0
        prefix = text[prefix_start:start]
        lokasi_matches = list(re.finditer(r"(?im)^\s*Lokasi\s*:", prefix))
        if lokasi_matches:
            segment_start = prefix_start + lokasi_matches[-1].start()
        starts.append(segment_start)

    segments = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(text)
        segments.append(text[start:end])
    return segments


def _extract_declared_unit_qty(chat_text: str) -> int:
    m = re.search(r"(?im)^\s*(\d{1,3})\s*unit\b", _clean(chat_text))
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _segment_identity(segment_text: str) -> Dict:
    text = _clean(segment_text)

    driver = ""
    plate = ""
    phone = ""

    driver_match = re.search(r"(?im)^\s*(?:driver|pengemudi)(?:\s*\d+)?\s*[:.]?\s*([^\n\r]+)", text)
    if driver_match:
        driver = driver_match.group(1)

    plate_match = re.search(
        r"(?im)^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*[:.]?\s*([^\n\r]+)",
        text,
    )
    if plate_match:
        plate = plate_match.group(1)

    phone_match = re.search(
        r"(?im)^\s*(?:no\.?\s*hp|hp|no\.?\s*telp|no\.?\s*tlp|kontak)\s*[:.]?\s*([^\n\r]+)",
        text,
    )
    if phone_match:
        phone = phone_match.group(1)

    return {
        "driver": _norm_text(driver),
        "no_plat": _norm_plate(plate),
        "kontak_driver": _norm_phone(phone),
    }


def _revision_segment_identities(chat_text: str) -> List[Dict]:
    return [_segment_identity(segment) for segment in _loading_segments_from_chat(chat_text)]


def _identity_overlap_count(left: Dict, right: Dict) -> int:
    count = 0
    for field in ("driver", "no_plat", "kontak_driver"):
        left_val = left.get(field, "")
        right_val = right.get(field, "")
        if left_val and right_val and left_val == right_val:
            count += 1
    return count


def _match_row_to_revision_segment(incoming_norm: Dict, segment_identities: List[Dict]) -> Optional[int]:
    incoming_identity = {
        "driver": _norm_text(incoming_norm.get("driver", "")),
        "no_plat": _norm_plate(incoming_norm.get("no_plat", "")),
        "kontak_driver": _norm_phone(incoming_norm.get("kontak_driver", "")),
    }

    best_idx = None
    best_score = 0
    tied = False
    for idx, segment_identity in enumerate(segment_identities):
        score = _identity_overlap_count(incoming_identity, segment_identity)
        if score > best_score:
            best_idx = idx
            best_score = score
            tied = False
        elif score == best_score and score > 0:
            tied = True

    if best_idx is None or best_score <= 0 or tied:
        return None
    return best_idx


def _revision_marker_segment_indexes(chat_text: str) -> set:
    if not _looks_like_revision(chat_text):
        return set()

    segments = _loading_segments_from_chat(chat_text)
    if len(segments) <= 1:
        return set()

    return {
        idx
        for idx, segment in enumerate(segments)
        if _has_explicit_revision_marker(segment or "")
    }


def _has_identity_payload(norm_row: Dict) -> bool:
    return any(
        not _is_blank(norm_row.get(field))
        for field in ("driver", "no_plat", "kontak_driver")
    )


def _has_operational_payload(norm_row: Dict) -> bool:
    return any(
        not _is_blank(norm_row.get(field))
        for field in (
            "tgl_ro",
            "tgl_muat",
            "pickup",
            "tujuan",
            "no_plat",
            "type_truck",
            "driver",
            "kontak_driver",
        )
    )


def _incoming_identity_fully_matches_row(existing_row: OrderDataset, incoming_norm: Dict) -> bool:
    row_norm = _dataset_to_norm_row(existing_row)

    checks = []
    incoming_driver = _norm_text(incoming_norm.get("driver", ""))
    incoming_plate = _norm_plate(incoming_norm.get("no_plat", ""))
    incoming_phone = _norm_phone(incoming_norm.get("kontak_driver", ""))

    if incoming_driver:
        checks.append(_norm_text(row_norm["driver"]) == incoming_driver)
    if incoming_plate:
        checks.append(_norm_plate(row_norm["no_plat"]) == incoming_plate)
    if incoming_phone:
        checks.append(_norm_phone(row_norm["kontak_driver"]) == incoming_phone)

    return bool(checks) and all(checks)


def _rows_equal_for_exact_duplicate(existing_row: OrderDataset, incoming_norm: Dict) -> bool:
    existing_norm = _dataset_to_norm_row(existing_row)
    return (
        _norm_text(existing_norm["tgl_ro"]) == _norm_text(incoming_norm["tgl_ro"])
        and _norm_text(existing_norm["tgl_muat"]) == _norm_text(incoming_norm["tgl_muat"])
        and _norm_text(existing_norm["pickup"]) == _norm_text(incoming_norm["pickup"])
        and _norm_text(existing_norm["tujuan"]) == _norm_text(incoming_norm["tujuan"])
        and _norm_plate(existing_norm["no_plat"]) == _norm_plate(incoming_norm["no_plat"])
        and _norm_text(existing_norm["type_truck"]) == _norm_text(incoming_norm["type_truck"])
        and _norm_text(existing_norm["driver"]) == _norm_text(incoming_norm["driver"])
        and _norm_phone(existing_norm["kontak_driver"]) == _norm_phone(incoming_norm["kontak_driver"])
    )


def _existing_status_for_matching(existing_row: OrderDataset) -> str:
    explicit = _normalize_status(existing_row.status_unit or "")
    if explicit:
        return explicit
    return _derive_status(_dataset_to_norm_row(existing_row))


def _apply_row_update(existing_row: OrderDataset, incoming_norm: Dict, allow_overwrite: bool) -> bool:
    changed = False

    def _set_if_allowed(attr_name: str, incoming_value: str, normalizer):
        nonlocal changed
        incoming_clean = _clean(incoming_value)
        if _is_blank(incoming_clean):
            return

        current_clean = _clean(getattr(existing_row, attr_name, ""))
        if _is_blank(current_clean):
            setattr(existing_row, attr_name, incoming_clean)
            changed = True
            return

        if allow_overwrite and normalizer(current_clean) != normalizer(incoming_clean):
            setattr(existing_row, attr_name, incoming_clean)
            changed = True

    # Identity fields: refill by default; overwrite only for explicit revision context.
    _set_if_allowed("driver", incoming_norm.get("driver", ""), _norm_text)
    _set_if_allowed("no_plat", incoming_norm.get("no_plat", ""), _norm_plate)
    _set_if_allowed("kontak_driver", incoming_norm.get("kontak_driver", ""), _norm_phone)

    # Context fields only diisi jika kosong, tidak dioverwrite agar aman.
    _set_if_allowed("tgl_ro", incoming_norm.get("tgl_ro", ""), _norm_text)
    _set_if_allowed("tgl_muat", incoming_norm.get("tgl_muat", ""), _norm_text)
    _set_if_allowed("pickup", incoming_norm.get("pickup", ""), _norm_text)
    _set_if_allowed("tujuan", incoming_norm.get("tujuan", ""), _norm_text)
    _set_if_allowed("type_truck", incoming_norm.get("type_truck", ""), _norm_text)

    if changed:
        month_segment, year_segment = extract_month_year_from_tgl_muat(existing_row.tgl_muat)
        existing_row.month_segment = month_segment
        existing_row.year_segment = year_segment
        existing_row.status_unit = _derive_status(_dataset_to_norm_row(existing_row))

    return changed


def _match_and_update_existing_row(
    existing_rows: List[OrderDataset],
    incoming_norm: Dict,
    is_revision_context: bool,
    consumed_ids: set,
    revision_segment_index: Optional[int] = None,
    revision_group_size: int = 0,
    revision_old_anchors: Optional[Dict[str, str]] = None,
) -> bool:
    if not _has_identity_payload(incoming_norm):
        return False

    incoming_plate = _norm_plate(incoming_norm.get("no_plat", ""))
    incoming_driver = _norm_text(incoming_norm.get("driver", ""))
    incoming_phone = _norm_phone(incoming_norm.get("kontak_driver", ""))
    revision_context_override_ids = set()

    if is_revision_context and revision_old_anchors:
        anchor_matches = []
        has_static_context = any(
            not _is_blank(incoming_norm.get(field))
            for field in ("tgl_ro", "tgl_muat", "pickup", "tujuan", "type_truck")
        )
        for row in existing_rows:
            if row.id in consumed_ids:
                continue
            row_norm = _dataset_to_norm_row(row)
            matched_anchor = False

            old_plate = _norm_plate(revision_old_anchors.get("no_plat", ""))
            if old_plate and _norm_plate(row_norm["no_plat"]) == old_plate:
                matched_anchor = True

            old_phone = _norm_phone(revision_old_anchors.get("kontak_driver", ""))
            if old_phone and _norm_phone(row_norm["kontak_driver"]) == old_phone:
                matched_anchor = True

            if not matched_anchor:
                continue

            if has_static_context and _row_context_score(row, incoming_norm) < 3:
                continue
            anchor_matches.append(row)

        if len(anchor_matches) == 1:
            target_row = anchor_matches[0]
            changed = _apply_row_update(
                existing_row=target_row,
                incoming_norm=incoming_norm,
                allow_overwrite=True,
            )
            if changed:
                consumed_ids.add(target_row.id)
            return changed

    if is_revision_context and revision_segment_index is not None:
        positional_candidates = []
        for row in existing_rows:
            context_score = _row_context_score(row, incoming_norm)
            if context_score < 5:
                continue
            positional_candidates.append(row)

        if revision_group_size and len(positional_candidates) > revision_group_size:
            positional_candidates = positional_candidates[-revision_group_size:]

        if 0 <= revision_segment_index < len(positional_candidates):
            target_row = positional_candidates[revision_segment_index]
            changed = _apply_row_update(
                existing_row=target_row,
                incoming_norm=incoming_norm,
                allow_overwrite=True,
            )
            if changed:
                consumed_ids.add(target_row.id)
            return changed

    if is_revision_context:
        override_candidates = []
        for row in existing_rows:
            if row.id in consumed_ids:
                continue
            if _existing_status_for_matching(row) != "ASSIGNED":
                continue

            context_score = _row_context_score(row, incoming_norm)
            if context_score < 7:
                continue

            row_norm = _dataset_to_norm_row(row)
            row_plate = _norm_plate(row_norm["no_plat"])
            row_driver = _norm_text(row_norm["driver"])
            row_phone = _norm_phone(row_norm["kontak_driver"])
            can_override = (
                (incoming_driver and row_driver and incoming_driver != row_driver)
                or (incoming_plate and row_plate and incoming_plate != row_plate)
                or (incoming_phone and row_phone and incoming_phone != row_phone)
            )
            if can_override:
                override_candidates.append(row)

        if len(override_candidates) == 1:
            revision_context_override_ids.add(override_candidates[0].id)

    # Guard: jika identitas incoming sama persis dengan row existing,
    # perlakukan sebagai duplicate info dan jangan isi slot partial lain.
    #
    # Aturan:
    # - Skor konteks >= 3 -> langsung dianggap duplikat.
    # - Skor konteks 2 -> hanya dianggap duplikat bila incoming membawa
    #   sinyal tanggal (RO/Muat), supaya order valid dengan konteks mirip
    #   tapi tanpa tanggal tidak ikut ter-skip.
    incoming_has_date_signal = (
        (not _is_blank(incoming_norm.get("tgl_ro", "")))
        or (not _is_blank(incoming_norm.get("tgl_muat", "")))
    )
    for row in existing_rows:
        context_score = _row_context_score(row, incoming_norm)
        if context_score < 2:
            continue
        if context_score == 2 and not incoming_has_date_signal:
            continue
        if _incoming_identity_fully_matches_row(row, incoming_norm):
            consumed_ids.add(row.id)
            return True

    best_row = None
    best_priority = -1
    best_score = -999

    for row in existing_rows:
        if row.id in consumed_ids:
            continue

        status = _existing_status_for_matching(row)
        context_score = _row_context_score(row, incoming_norm)
        if context_score < 3:
            continue

        row_norm = _dataset_to_norm_row(row)
        row_plate = _norm_plate(row_norm["no_plat"])
        row_driver = _norm_text(row_norm["driver"])
        row_phone = _norm_phone(row_norm["kontak_driver"])

        # Priority 3: exact plate (bisa update assigned kalau revision explicit)
        if incoming_plate and row_plate and incoming_plate == row_plate:
            if status in {"PARTIAL", "UNASSIGNED"} or is_revision_context:
                priority = 3
            else:
                priority = -1
        # Priority 2: same driver+phone identity, but only for explicit revisions.
        elif (
            is_revision_context
            and incoming_driver
            and incoming_phone
            and row_driver == incoming_driver
            and row_phone == incoming_phone
        ):
            priority = 2
        # Priority 1: explicit revision may replace assigned identity only
        # when stable context points to one existing row.
        elif is_revision_context and row.id in revision_context_override_ids:
            priority = 1
        # Priority 1: fill slot partial/unassigned by context.
        elif status in {"PARTIAL", "UNASSIGNED"}:
            can_fill = (
                (incoming_driver and _is_blank(row_norm["driver"]))
                or (incoming_plate and _is_blank(row_norm["no_plat"]))
                or (incoming_phone and _is_blank(row_norm["kontak_driver"]))
            )
            # In revision context we also allow replacement when context sangat cocok.
            can_override = (
                is_revision_context
                and (
                    (incoming_driver and row_driver and incoming_driver != row_driver)
                    or (incoming_plate and row_plate and incoming_plate != row_plate)
                    or (incoming_phone and row_phone and incoming_phone != row_phone)
                )
            )
            priority = 1 if (can_fill or can_override) else -1
        else:
            priority = -1

        if priority < 0:
            continue

        # Prefer more incomplete rows for refill.
        missing_identity = 0
        if _is_blank(row_norm["driver"]):
            missing_identity += 1
        if _is_blank(row_norm["no_plat"]):
            missing_identity += 1
        if _is_blank(row_norm["kontak_driver"]):
            missing_identity += 1

        effective_score = context_score * 10 + missing_identity
        if priority > best_priority or (priority == best_priority and effective_score > best_score):
            best_row = row
            best_priority = priority
            best_score = effective_score

    if best_row is None:
        return False

    changed = _apply_row_update(
        existing_row=best_row,
        incoming_norm=incoming_norm,
        allow_overwrite=is_revision_context,
    )
    if changed:
        consumed_ids.add(best_row.id)
    return changed


def _consume_existing_partial_placeholder(
    existing_rows: List[OrderDataset],
    incoming_norm: Dict,
    consumed_ids: set,
) -> bool:
    """
    Untuk row incoming tanpa identitas (driver/plat/phone kosong),
    jangan tambah row baru bila masih ada slot partial existing pada konteks yang sama.
    """
    if _has_identity_payload(incoming_norm):
        return False

    best_row = None
    best_score = -999

    for row in existing_rows:
        if row.id in consumed_ids:
            continue

        status = _existing_status_for_matching(row)
        if status not in {"PARTIAL", "UNASSIGNED"}:
            continue

        context_score = _row_context_score(row, incoming_norm)
        if context_score < 3:
            continue

        row_norm = _dataset_to_norm_row(row)
        if not (
            _is_blank(row_norm["driver"])
            or _is_blank(row_norm["no_plat"])
            or _is_blank(row_norm["kontak_driver"])
        ):
            continue

        missing_identity = 0
        if _is_blank(row_norm["driver"]):
            missing_identity += 1
        if _is_blank(row_norm["no_plat"]):
            missing_identity += 1
        if _is_blank(row_norm["kontak_driver"]):
            missing_identity += 1

        score = context_score * 10 + missing_identity
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None:
        return False

    consumed_ids.add(best_row.id)
    return True


def generate_chat_hash(chat_text: str) -> str:
    normalized = (chat_text or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_month_year_from_tgl_muat(tgl_muat: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not tgl_muat:
        return None, None

    text = str(tgl_muat).strip().upper()

    # Pattern: DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r"\b\d{1,2}[/-](\d{1,2})[/-](\d{2,4})\b", text)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if year < 100:
            year += 2000
        return month, year

    # Pattern: DD MON YYYY (e.g. 05 FEBRUARI 2026)
    m = re.search(r"\b\d{1,2}\s+([A-Z]+)\s+(\d{2,4})\b", text)
    if m:
        month = _MONTH_MAP.get(m.group(1))
        year = int(m.group(2))
        if year < 100:
            year += 2000
        return month, year

    return None, None


def _to_uuid(value):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


def prepare_chat_for_parsing(chat_text: str) -> Tuple[bool, Optional[uuid.UUID]]:
    """
    Deduplication gate before parser runs.

    Returns:
        (should_parse, raw_chat_id)
    """
    chat_hash = generate_chat_hash(chat_text)
    session = SessionLocal()
    try:
        existing = session.query(RawChat).filter(RawChat.chat_hash == chat_hash).first()
        if existing:
            return False, existing.id

        row = RawChat(chat_hash=chat_hash, chat_text=chat_text)
        session.add(row)
        session.commit()
        session.refresh(row)
        return True, row.id
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def find_raw_chat_id(chat_text: str) -> Optional[uuid.UUID]:
    chat_hash = generate_chat_hash(chat_text)
    session = SessionLocal()
    try:
        existing = session.query(RawChat).filter(RawChat.chat_hash == chat_hash).first()
        return existing.id if existing is not None else None
    except SQLAlchemyError:
        return None
    finally:
        session.close()


def update_raw_chat_extraction_elapsed(
    raw_chat_id,
    elapsed_ms: float | None = None,
    run_id: str | None = None,
    run_elapsed_ms: float | None = None,
) -> bool:
    raw_chat_uuid = _to_uuid(raw_chat_id)
    if raw_chat_uuid is None:
        return False
    try:
        elapsed_value = float(elapsed_ms or 0.0) if elapsed_ms is not None else 0.0
    except Exception:
        elapsed_value = 0.0
    try:
        run_elapsed_value = float(run_elapsed_ms or 0.0) if run_elapsed_ms is not None else 0.0
    except Exception:
        run_elapsed_value = 0.0
    clean_run_id = _clean(run_id)
    if elapsed_value <= 0 and run_elapsed_value <= 0 and not clean_run_id:
        return False

    session = SessionLocal()
    try:
        row = session.query(RawChat).filter(RawChat.id == raw_chat_uuid).first()
        if row is None:
            return False
        if elapsed_value > 0:
            row.extraction_elapsed_ms = elapsed_value
        if clean_run_id:
            row.extraction_run_id = clean_run_id
        if run_elapsed_value > 0:
            row.extraction_run_elapsed_ms = run_elapsed_value
        session.commit()
        return True
    except SQLAlchemyError:
        session.rollback()
        return False
    finally:
        session.close()


def _iter_rows(parsed_rows: Iterable[Dict]):
    # Support list[dict] and pandas.DataFrame without importing pandas explicitly.
    if hasattr(parsed_rows, "to_dict"):
        return parsed_rows.to_dict(orient="records")
    return parsed_rows


def _normalize_row_keys(row: Dict) -> Dict:
    if not isinstance(row, dict):
        return {
            "job_number": "",
            "tgl_ro": "",
            "tgl_muat": "",
            "pickup": "",
            "tujuan": "",
            "no_plat": "",
            "type_truck": "",
            "driver": "",
            "kontak_driver": "",
            "status_unit": "",
        }

    # Support parser-style keys and Office table keys.
    return {
        "job_number": _clean(row.get("job_number", row.get("Job Number", ""))),
        "tgl_ro": _clean(row.get("tgl_ro", row.get("Tgl RO", ""))),
        "tgl_muat": _clean(row.get("tgl_muat", row.get("Tgl Muat", ""))),
        "pickup": _clean(row.get("pickup", row.get("Pickup", ""))),
        "tujuan": _clean(row.get("tujuan", row.get("Tujuan", ""))),
        "no_plat": _clean(row.get("no_plat", row.get("No. Plat", ""))),
        "type_truck": _clean(row.get("type_truck", row.get("Type Truck", ""))),
        "driver": _clean(row.get("driver", row.get("Driver", ""))),
        "kontak_driver": _clean(row.get("kontak_driver", row.get("Kontak Driver", ""))),
        "status_unit": _clean(row.get("status_unit", row.get("status_unit", ""))),
    }


def _row_base_key(norm_row: Dict) -> str:
    # Deliberately ignore job_number; it can be regenerated by UI mode.
    fields = [
        norm_row.get("tgl_ro", "").upper(),
        norm_row.get("tgl_muat", "").upper(),
        norm_row.get("pickup", "").upper(),
        norm_row.get("tujuan", "").upper(),
        norm_row.get("no_plat", "").upper(),
        norm_row.get("type_truck", "").upper(),
        norm_row.get("driver", "").upper(),
        norm_row.get("kontak_driver", "").upper(),
        norm_row.get("status_unit", "").upper(),
    ]
    return "|".join(fields)


def _stage2_norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize_dates_for_key(_clean(value)).lower())


def _stage2_candidate_key_from_norm(norm_row: Dict) -> str:
    return "|".join(
        [
            _stage2_norm_key(norm_row.get("tgl_ro", "")),
            _stage2_norm_key(norm_row.get("pickup", "")),
            _stage2_norm_key(norm_row.get("tujuan", "")),
            _stage2_norm_key(norm_row.get("type_truck", "")),
        ]
    )


def _stage2_candidate_key_from_dataset(row: OrderDataset) -> str:
    return _stage2_candidate_key_from_norm(_dataset_to_norm_row(row))


def _stage2_identity_tokens(norm_row: Dict) -> set:
    tokens = set()
    for field in ("no_plat", "kontak_driver", "driver"):
        value = _stage2_norm_key(norm_row.get(field, ""))
        if value:
            tokens.add(f"{field}:{value}")
    return tokens


def _stage2_identity_signature(norm_row: Dict) -> Dict[str, str]:
    return {
        "driver": _stage2_norm_key(norm_row.get("driver", "")),
        "no_plat": _stage2_norm_key(norm_row.get("no_plat", "")),
        "kontak_driver": _stage2_norm_key(norm_row.get("kontak_driver", "")),
    }


def _stage2_identity_is_duplicate(existing: Dict[str, str], incoming: Dict[str, str]) -> bool:
    # Plat kendaraan adalah identitas unit paling kuat. Phone saja tidak cukup,
    # karena output NER bisa bergeser pada daftar nomor HP berurutan.
    if existing.get("no_plat") and incoming.get("no_plat") and existing["no_plat"] == incoming["no_plat"]:
        return True

    same_fields = 0
    for field in ("driver", "no_plat", "kontak_driver"):
        if existing.get(field) and incoming.get(field) and existing[field] == incoming[field]:
            same_fields += 1
    return same_fields >= 2


def _identity_fields_complete(norm_row: Dict) -> bool:
    return all(
        not _is_blank(norm_row.get(field))
        for field in ("driver", "no_plat", "kontak_driver")
    )


def apply_stage2_match_fill(candidate_key: str, incoming_rows: Iterable[Dict]) -> Dict[str, int]:
    """
    Apply hasil matcher tahap 2: isi slot partial pada order lama.

    Fungsi ini hanya mengisi row existing yang masih PARTIAL/UNASSIGNED dan tidak
    membuat row baru. Penyimpanan batch susulan tetap dikontrol oleh caller.
    """
    candidate_key = _clean(candidate_key)
    if not candidate_key:
        return {"filled": 0, "duplicates": 0, "skipped": 0}

    incoming_norms = [
        _normalize_row_keys(row)
        for row in _iter_rows(incoming_rows)
        if isinstance(row, dict)
    ]
    incoming_complete = [row for row in incoming_norms if _identity_fields_complete(row)]
    if not incoming_complete:
        return {"filled": 0, "duplicates": 0, "skipped": len(incoming_norms)}

    session = SessionLocal()
    filled = 0
    duplicates = 0
    skipped = 0
    try:
        candidate_rows: List[OrderDataset] = [
            row
            for row in session.query(OrderDataset)
            .outerjoin(RawChat, OrderDataset.raw_chat_id == RawChat.id)
            .order_by(
                RawChat.created_at.asc().nullsfirst(),
                OrderDataset.batch_row_order.asc().nullsfirst(),
                OrderDataset.created_at.asc(),
                OrderDataset.id.asc(),
            )
            .all()
            if _stage2_candidate_key_from_dataset(row) == candidate_key
        ]
        if not candidate_rows:
            return {"filled": 0, "duplicates": 0, "skipped": len(incoming_complete)}

        existing_identities = [
            _stage2_identity_signature(_dataset_to_norm_row(row))
            for row in candidate_rows
        ]

        targets = [
            row
            for row in candidate_rows
            if _existing_status_for_matching(row) in {"PARTIAL", "UNASSIGNED"}
        ]
        consumed_target_ids = set()

        for incoming_norm in incoming_complete:
            incoming_identity = _stage2_identity_signature(incoming_norm)
            if any(
                _stage2_identity_is_duplicate(existing_identity, incoming_identity)
                for existing_identity in existing_identities
            ):
                duplicates += 1
                continue

            target = None
            for row in targets:
                if row.id in consumed_target_ids:
                    continue
                target = row
                break

            if target is None:
                skipped += 1
                continue

            if _apply_row_update(target, incoming_norm, allow_overwrite=False):
                filled += 1
                consumed_target_ids.add(target.id)
                existing_identities.append(incoming_identity)
            else:
                skipped += 1

        session.commit()
        return {"filled": filled, "duplicates": duplicates, "skipped": skipped}
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def _chat_scope_key(raw_chat_id) -> str:
    """
    Scope hash per raw chat upload.
    Ini mencegah bentrok hash antar upload batch berbeda yang kebetulan
    punya baris dengan field identik.
    """
    raw_uuid = _to_uuid(raw_chat_id)
    if raw_uuid is not None:
        return str(raw_uuid)

    fallback = _clean(raw_chat_id)
    return fallback if fallback else "global"


def _build_row_hash(base_key: str, occurrence: int, chat_scope: str) -> str:
    payload = f"{chat_scope}|{base_key}|occ:{occurrence}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def save_parsed_rows(
    raw_chat_id,
    parsed_rows: Iterable[Dict],
    allow_smart_merge: bool = True,
) -> int:
    """
    Persist parser output rows without changing parser field names.
    Expected row keys:
      job_number, tgl_ro, tgl_muat, pickup, tujuan,
      no_plat, type_truck, driver, kontak_driver, status_unit
    """
    session = SessionLocal()
    inserted = 0
    merged = 0
    occurrence_map: Dict[str, int] = {}
    raw_chat_uuid = _to_uuid(raw_chat_id)
    chat_scope = _chat_scope_key(raw_chat_uuid if raw_chat_uuid is not None else raw_chat_id)

    try:
        chat_text = ""
        if raw_chat_uuid is not None:
            raw_chat = session.query(RawChat).filter(RawChat.id == raw_chat_uuid).first()
            if raw_chat is not None:
                chat_text = _clean(raw_chat.chat_text)
        is_revision_context = _looks_like_revision(chat_text)
        revision_marker_indexes = _revision_marker_segment_indexes(chat_text)
        revision_segment_identities = _revision_segment_identities(chat_text)
        revision_group_size = _extract_declared_unit_qty(chat_text)
        revision_old_anchors = _extract_revision_old_anchors(chat_text)

        historical_rows: List[OrderDataset] = (
            session.query(OrderDataset)
            .outerjoin(RawChat, OrderDataset.raw_chat_id == RawChat.id)
            .order_by(
                RawChat.created_at.asc().nullsfirst(),
                OrderDataset.batch_row_order.asc().nullsfirst(),
                OrderDataset.created_at.asc(),
                OrderDataset.id.asc(),
            )
            .all()
        )
        consumed_ids = set()

        rows = list(_iter_rows(parsed_rows))
        processed_revision_segments = set()
        for row_index, raw_row in enumerate(rows):
            norm = _normalize_row_keys(raw_row)
            if not _has_operational_payload(norm):
                continue

            tgl_muat = norm.get("tgl_muat")
            month_segment, year_segment = extract_month_year_from_tgl_muat(tgl_muat)

            if allow_smart_merge and is_revision_context and revision_marker_indexes:
                segment_index = _match_row_to_revision_segment(norm, revision_segment_identities)
                if segment_index is None:
                    segment_index = row_index
                if segment_index not in revision_marker_indexes:
                    continue
                if segment_index in processed_revision_segments:
                    continue
                if _match_and_update_existing_row(
                    existing_rows=historical_rows,
                    incoming_norm=norm,
                    is_revision_context=True,
                    consumed_ids=consumed_ids,
                    revision_segment_index=segment_index,
                    revision_group_size=revision_group_size,
                    revision_old_anchors=revision_old_anchors,
                ):
                    merged += 1
                    processed_revision_segments.add(segment_index)
                continue

            # 1) Smart cross-batch merge (refill/revisi) without touching parser logic.
            if allow_smart_merge and _match_and_update_existing_row(
                existing_rows=historical_rows,
                incoming_norm=norm,
                is_revision_context=is_revision_context,
                consumed_ids=consumed_ids,
                revision_old_anchors=revision_old_anchors,
            ):
                merged += 1
                continue

            # 2) Untuk row placeholder (tanpa identitas), konsumsi slot partial existing dulu.
            if allow_smart_merge and _consume_existing_partial_placeholder(
                existing_rows=historical_rows,
                incoming_norm=norm,
                consumed_ids=consumed_ids,
            ):
                merged += 1
                continue

            # 3) Skip exact duplicates globally (lintas upload), not only within same chat scope.
            if _has_identity_payload(norm) and any(_rows_equal_for_exact_duplicate(ex, norm) for ex in historical_rows):
                continue

            base_key = _row_base_key(norm)
            occurrence_map[base_key] = occurrence_map.get(base_key, 0) + 1
            occ = occurrence_map[base_key]
            row_hash = _build_row_hash(base_key, occ, chat_scope)

            exists = session.query(OrderDataset.id).filter(OrderDataset.row_hash == row_hash).first()
            if exists:
                continue

            rec = OrderDataset(
                raw_chat_id=raw_chat_uuid,
                row_hash=row_hash,
                job_number=norm.get("job_number"),
                tgl_ro=norm.get("tgl_ro"),
                tgl_muat=tgl_muat,
                pickup=norm.get("pickup"),
                tujuan=norm.get("tujuan"),
                no_plat=norm.get("no_plat"),
                type_truck=norm.get("type_truck"),
                driver=norm.get("driver"),
                kontak_driver=norm.get("kontak_driver"),
                status_unit=norm.get("status_unit") or _derive_status(norm),
                month_segment=month_segment,
                year_segment=year_segment,
                batch_row_order=row_index + 1,
            )
            session.add(rec)
            inserted += 1

        session.commit()
        return inserted + merged
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def replace_parsed_rows(
    raw_chat_id,
    parsed_rows: Iterable[Dict],
    allow_smart_merge: bool = True,
) -> int:
    raw_chat_uuid = _to_uuid(raw_chat_id)
    if raw_chat_uuid is None:
        return save_parsed_rows(
            raw_chat_id,
            parsed_rows,
            allow_smart_merge=allow_smart_merge,
        )

    session = SessionLocal()
    try:
        session.query(OrderDataset).filter(OrderDataset.raw_chat_id == raw_chat_uuid).delete(
            synchronize_session=False
        )
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()

    return save_parsed_rows(
        raw_chat_uuid,
        parsed_rows,
        allow_smart_merge=allow_smart_merge,
    )


def load_all_order_rows() -> List[Dict]:
    session = SessionLocal()
    try:
        rows = (
            session.query(OrderDataset, RawChat.chat_text)
            .outerjoin(RawChat, OrderDataset.raw_chat_id == RawChat.id)
            .order_by(
                RawChat.created_at.asc().nullsfirst(),
                OrderDataset.batch_row_order.asc().nullsfirst(),
                OrderDataset.created_at.asc(),
                OrderDataset.id.asc(),
            )
            .all()
        )
        result = []
        for r, chat_text in rows:
            norm = _dataset_to_norm_row(r)
            if not _has_operational_payload(norm):
                continue
            result.append(
                {
                    "raw_chat_id": str(r.raw_chat_id) if r.raw_chat_id else "",
                    "raw_chat_text": _clean(chat_text),
                    "job_number": _clean(r.job_number),
                    "tgl_ro": _clean(r.tgl_ro),
                    "tgl_muat": _clean(r.tgl_muat),
                    "pickup": _clean(r.pickup),
                    "tujuan": _clean(r.tujuan),
                    "no_plat": _clean(r.no_plat),
                    "type_truck": _clean(r.type_truck),
                    "driver": _clean(r.driver),
                    "kontak_driver": _clean(r.kontak_driver),
                    "status_unit": _clean(r.status_unit),
                }
            )
        return result
    except SQLAlchemyError:
        return []
    finally:
        session.close()


def load_latest_raw_chat_text() -> str:
    session = SessionLocal()
    try:
        row = (
            session.query(RawChat)
            .order_by(RawChat.created_at.desc(), RawChat.id.desc())
            .first()
        )
        return _clean(row.chat_text) if row is not None else ""
    except SQLAlchemyError:
        return ""
    finally:
        session.close()


def load_all_raw_chat_texts() -> List[str]:
    session = SessionLocal()
    try:
        rows = (
            session.query(RawChat)
            .order_by(RawChat.created_at.asc(), RawChat.id.asc())
            .all()
        )
        return [_clean(row.chat_text) for row in rows if _clean(row.chat_text)]
    except SQLAlchemyError:
        return []
    finally:
        session.close()


def load_all_raw_chat_records() -> List[Dict[str, str]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(RawChat)
            .order_by(RawChat.created_at.asc(), RawChat.id.asc())
            .all()
        )
        records = []
        for row in rows:
            chat_text = _clean(row.chat_text)
            if not chat_text:
                continue
            created_at = row.created_at.isoformat(sep=" ") if row.created_at else ""
            records.append(
                {
                    "id": str(row.id),
                    "created_at": created_at,
                    "extraction_elapsed_ms": float(row.extraction_elapsed_ms or 0.0),
                    "extraction_run_id": _clean(row.extraction_run_id),
                    "extraction_run_elapsed_ms": float(row.extraction_run_elapsed_ms or 0.0),
                    "chat_text": chat_text,
                }
            )
        return records
    except SQLAlchemyError:
        return []
    finally:
        session.close()


def save_stage2_match_audits(raw_chat_id, audit_rows: Iterable[Dict]) -> int:
    """
    Append audit hasil sequence-pair matcher tanpa mengubah row order.
    """
    rows = list(_iter_rows(audit_rows))
    if not rows:
        return 0

    session = SessionLocal()
    raw_uuid = _to_uuid(raw_chat_id)
    inserted = 0
    try:
        for row in rows:
            if not isinstance(row, dict):
                continue
            rec = Stage2MatchAudit(
                raw_chat_id=raw_uuid,
                candidate_key=_clean(row.get("candidate_key", "")),
                candidate_summary=_clean(row.get("candidate_summary", "")),
                order_state_text=_clean(row.get("order_state_text", "")),
                incoming_text=_clean(row.get("incoming_text", "")),
                predicted_label=_clean(row.get("predicted_label", "")),
                p_match=float(row.get("p_match", 0.0) or 0.0),
                p_no_match=float(row.get("p_no_match", 0.0) or 0.0),
                confidence=float(row.get("confidence", 0.0) or 0.0),
                action=_clean(row.get("action", "")),
                decision_status=_clean(row.get("decision_status", "")),
                policy_reason=_clean(row.get("policy_reason", "")),
                before_rows_json=_json_dump(row.get("before_rows", [])),
                after_rows_json=_json_dump(row.get("after_rows", [])),
                incoming_rows_json=_json_dump(row.get("incoming_rows", [])),
                candidate_source_rows_json=_json_dump(row.get("candidate_source_rows", [])),
                proposed_fill_count=int(row.get("proposed_fill_count", 0) or 0),
                incoming_complete_units=int(row.get("incoming_complete_units", 0) or 0),
                duplicate_units=int(row.get("duplicate_units", 0) or 0),
                overflow_units=int(row.get("overflow_units", 0) or 0),
                review_required=bool(row.get("review_required", False)),
            )
            session.add(rec)
            inserted += 1
        session.commit()
        return inserted
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


def load_stage2_match_audits(limit: int = 100) -> List[Dict]:
    session = SessionLocal()
    try:
        rows = (
            session.query(Stage2MatchAudit)
            .order_by(Stage2MatchAudit.created_at.desc(), Stage2MatchAudit.id.desc())
            .limit(max(1, int(limit or 100)))
            .all()
        )
        return [
            {
                "id": str(row.id),
                "raw_chat_id": str(row.raw_chat_id) if row.raw_chat_id else "",
                "candidate_key": _clean(row.candidate_key),
                "candidate_summary": _clean(row.candidate_summary),
                "order_state_text": _clean(row.order_state_text),
                "incoming_text": _clean(row.incoming_text),
                "predicted_label": _clean(row.predicted_label),
                "p_match": float(row.p_match or 0.0),
                "p_no_match": float(row.p_no_match if row.p_no_match is not None else max(0.0, 1.0 - float(row.p_match or 0.0))),
                "confidence": float(row.confidence or 0.0),
                "action": _clean(row.action),
                "decision_status": _clean(row.decision_status),
                "policy_reason": _clean(row.policy_reason),
                "before_rows": _json_load(row.before_rows_json),
                "after_rows": _json_load(row.after_rows_json),
                "incoming_rows": _json_load(row.incoming_rows_json),
                "candidate_source_rows": _json_load(row.candidate_source_rows_json),
                "proposed_fill_count": int(row.proposed_fill_count or 0),
                "incoming_complete_units": int(row.incoming_complete_units or 0),
                "duplicate_units": int(row.duplicate_units or 0),
                "overflow_units": int(row.overflow_units or 0),
                "review_required": bool(row.review_required),
                "created_at": row.created_at.isoformat(sep=" ") if row.created_at else "",
            }
            for row in rows
        ]
    except SQLAlchemyError:
        return []
    finally:
        session.close()


def reset_all_data() -> Dict[str, int]:
    """
    Reset seluruh data parser yang tersimpan agar database kembali kosong.
    """
    session = SessionLocal()
    try:
        deleted_match_audits = session.query(Stage2MatchAudit).delete(synchronize_session=False)
        deleted_order_rows = session.query(OrderDataset).delete(synchronize_session=False)
        deleted_raw_chats = session.query(RawChat).delete(synchronize_session=False)
        session.commit()
        return {
            "stage2_match_audits_deleted": int(deleted_match_audits or 0),
            "order_dataset_deleted": int(deleted_order_rows or 0),
            "raw_chats_deleted": int(deleted_raw_chats or 0),
        }
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()



