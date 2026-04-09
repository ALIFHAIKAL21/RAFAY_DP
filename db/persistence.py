import hashlib
import re
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from db.database import SessionLocal
from models.order_dataset import OrderDataset
from models.raw_chat import RawChat


_MONTH_MAP = {
    "JAN": 1,
    "JANUARI": 1,
    "FEB": 2,
    "FEBRUARI": 2,
    "MAR": 3,
    "MARET": 3,
    "APR": 4,
    "APRIL": 4,
    "MEI": 5,
    "JUN": 6,
    "JUNI": 6,
    "JUL": 7,
    "JULI": 7,
    "AGS": 8,
    "AGUSTUS": 8,
    "AUG": 8,
    "SEP": 9,
    "SEPT": 9,
    "SEPTEMBER": 9,
    "OKT": 10,
    "OKTOBER": 10,
    "OCT": 10,
    "NOV": 11,
    "NOVEMBER": 11,
    "DES": 12,
    "DESEMBER": 12,
    "DEC": 12,
}

_REVISION_KEYWORDS_PATTERN = re.compile(
    r"\b(rev|revisi|revision|update|ubah|ganti|perbaikan)\b",
    re.IGNORECASE,
)


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


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
        score += 3 if _norm_text(existing_norm["tgl_muat"]) == _norm_text(incoming_norm["tgl_muat"]) else -3

    if not _is_blank(existing_norm["tgl_ro"]) and not _is_blank(incoming_norm["tgl_ro"]):
        score += 2 if _norm_text(existing_norm["tgl_ro"]) == _norm_text(incoming_norm["tgl_ro"]) else -2

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


def _has_identity_payload(norm_row: Dict) -> bool:
    return any(
        not _is_blank(norm_row.get(field))
        for field in ("driver", "no_plat", "kontak_driver")
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
) -> bool:
    if not _has_identity_payload(incoming_norm):
        return False

    incoming_plate = _norm_plate(incoming_norm.get("no_plat", ""))
    incoming_driver = _norm_text(incoming_norm.get("driver", ""))
    incoming_phone = _norm_phone(incoming_norm.get("kontak_driver", ""))

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


def save_parsed_rows(raw_chat_id, parsed_rows: Iterable[Dict]) -> int:
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

        historical_rows: List[OrderDataset] = (
            session.query(OrderDataset)
            .order_by(OrderDataset.created_at.asc(), OrderDataset.id.asc())
            .all()
        )
        consumed_ids = set()

        rows = list(_iter_rows(parsed_rows))
        for raw_row in rows:
            norm = _normalize_row_keys(raw_row)
            tgl_muat = norm.get("tgl_muat")
            month_segment, year_segment = extract_month_year_from_tgl_muat(tgl_muat)

            # 1) Smart cross-batch merge (refill/revisi) without touching parser logic.
            if _match_and_update_existing_row(
                existing_rows=historical_rows,
                incoming_norm=norm,
                is_revision_context=is_revision_context,
                consumed_ids=consumed_ids,
            ):
                merged += 1
                continue

            # 2) Untuk row placeholder (tanpa identitas), konsumsi slot partial existing dulu.
            if _consume_existing_partial_placeholder(
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


def load_all_order_rows() -> List[Dict]:
    session = SessionLocal()
    try:
        rows = (
            session.query(OrderDataset)
            .order_by(OrderDataset.created_at.asc(), OrderDataset.id.asc())
            .all()
        )
        return [
            {
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
            for r in rows
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
        deleted_order_rows = session.query(OrderDataset).delete(synchronize_session=False)
        deleted_raw_chats = session.query(RawChat).delete(synchronize_session=False)
        session.commit()
        return {
            "order_dataset_deleted": int(deleted_order_rows or 0),
            "raw_chats_deleted": int(deleted_raw_chats or 0),
        }
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()



