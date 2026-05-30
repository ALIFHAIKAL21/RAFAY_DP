import streamlit as st
import pandas as pd
from io import BytesIO
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import time

# Setup Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))


from src.inference.batch_processor import ChatBatchProcessor
from src.inference.event_classifier import EventClassifierInference
from src.inference.revision_matcher import RevisionMatcherInference

try:
    from db.persistence import load_all_order_rows as db_load_all_order_rows
    from db.persistence import prepare_chat_for_parsing as db_prepare_chat_for_parsing
    from db.persistence import reset_all_data as db_reset_all_data
    from db.persistence import save_parsed_rows as db_save_parsed_rows
    from db.session import init_db as db_init_db
    DB_PERSISTENCE_ENABLED = True
except Exception:
    db_load_all_order_rows = None
    db_prepare_chat_for_parsing = None
    db_reset_all_data = None
    db_save_parsed_rows = None
    db_init_db = None
    DB_PERSISTENCE_ENABLED = False

# Optional override khusus app.py untuk A/B test model.
# Default diarahkan ke model NER utama (indobert_NER), lalu fallback ke legacy tahap2.
_env_app_model_path = os.getenv("RAFAY_APP_MODEL_PATH", "").strip()
_default_ner_model = ROOT_DIR / "models" / "indobert_NER" / "final_model"
_legacy_tahap2_model = ROOT_DIR / "models" / "indobert_tahap2" / "final_model"
_resolved_default_ner_model = _default_ner_model if _default_ner_model.exists() else _legacy_tahap2_model
if _env_app_model_path:
    _env_path = Path(_env_app_model_path)
    if _env_path.exists():
        APP_MODEL_PATH = str(_env_path)
    elif _resolved_default_ner_model.exists():
        print(f"[WARN] RAFAY_APP_MODEL_PATH tidak ditemukan: {_env_app_model_path}. Fallback ke model default NER.")
        APP_MODEL_PATH = str(_resolved_default_ner_model)
    else:
        APP_MODEL_PATH = ""
elif _resolved_default_ner_model.exists():
    APP_MODEL_PATH = str(_resolved_default_ner_model)
else:
    APP_MODEL_PATH = ""

_env_event_model_path = os.getenv("RAFAY_EVENT_MODEL_PATH", "").strip()
_default_event_model = ROOT_DIR / "models" / "indobert_event_classifier" / "final_model"
if _env_event_model_path:
    _event_env_path = Path(_env_event_model_path)
    APP_EVENT_MODEL_PATH = str(_event_env_path) if _event_env_path.exists() else _env_event_model_path
elif _default_event_model.exists():
    APP_EVENT_MODEL_PATH = str(_default_event_model)
else:
    APP_EVENT_MODEL_PATH = ""

try:
    APP_EVENT_THRESHOLD = float(os.getenv("RAFAY_EVENT_THRESHOLD", "0.75"))
except ValueError:
    APP_EVENT_THRESHOLD = 0.75

_env_revision_matcher_path = os.getenv("RAFAY_REVISION_MATCHER_MODEL_PATH", "").strip()
_default_revision_matcher = ROOT_DIR / "models" / "indobert_revision_matcher" / "final_model"
if _env_revision_matcher_path:
    _rev_env_path = Path(_env_revision_matcher_path)
    APP_REVISION_MATCHER_MODEL_PATH = str(_rev_env_path) if _rev_env_path.exists() else _env_revision_matcher_path
elif _default_revision_matcher.exists():
    APP_REVISION_MATCHER_MODEL_PATH = str(_default_revision_matcher)
else:
    APP_REVISION_MATCHER_MODEL_PATH = ""

try:
    APP_REVISION_MATCH_THRESHOLD = float(os.getenv("RAFAY_REVISION_MATCH_THRESHOLD", "0.58"))
except ValueError:
    APP_REVISION_MATCH_THRESHOLD = 0.58

try:
    APP_REVISION_MATCH_MIN_GAP = float(os.getenv("RAFAY_REVISION_MATCH_MIN_GAP", "0.05"))
except ValueError:
    APP_REVISION_MATCH_MIN_GAP = 0.05

APP_REVISION_ML_ENABLED = os.getenv("RAFAY_REVISION_ML_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
APP_REVISION_RULE_FALLBACK_ENABLED = os.getenv("RAFAY_REVISION_RULE_FALLBACK_ENABLED", "0").strip().lower() not in {"0", "false", "no"}

# --- KONFIGURASI RAFAY IDP v2.0 ---
DRIVER_BLACKLIST = ["RAFAY","AKBAR","ADMIN","JNE","LOGISTIK","EXPEDISI","PENGIRIM","ONCALL","REQUEST"]
_REVISION_MATCHER_INSTANCE = None
_REVISION_MATCHER_LOAD_FAILED = False
_EVENT_CLASSIFIER_INSTANCE = None
_EVENT_CLASSIFIER_LOAD_FAILED = False

# --- 0. HELPER FUNCTIONS ---
_FIELD_LABEL_ALIASES = {
    "Lokasi": [
        "lokasi", "loksi", "loaksi", "lokas", "lokasii", "lokasii", "lok"
    ],
    "Waktu loading": [
        "waktu loading", "waktu load", "waktu muat", "waktuloading",
        "wktu loading", "wkt loading", "wkatu loading", "waktu lodng",
        "waktu loadding", "waktu loding", "wktu loding"
    ],
    "Rute/tujuan": [
        "rute tujuan", "rute/tujuan", "rute tujuan", "rutetujuan",
        "rute tujan", "rute tujuam", "rute/tujan", "rute / tujuan",
        "route tujuan", "route/tujuan", "tujuan", "rute"
    ],
    "driver": [
        "driver", "ddriver", "drver", "drivr", "diver", "pengemudi", "sopir", "nama"
    ],
    "Nopol": [
        "nopol", "nopool", "nopel", "no pol", "no polisi", "no plat", "plat"
    ],
    "No hp": [
        "no hp", "nohp", "nomor hp", "hp", "no telp", "no tlp",
        "kontak", "no handphone", "no wa"
    ],
}

def _compact_label_token(text):
    s = str(text).lower()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s

def _levenshtein_limited(a, b, max_dist=2):
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_dist:
        return None
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        row_min = cur[0]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur_val = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + cost,
            )
            cur.append(cur_val)
            if cur_val < row_min:
                row_min = cur_val
        if row_min > max_dist:
            return None
        prev = cur
    dist = prev[-1]
    return dist if dist <= max_dist else None

def _normalize_field_label_token(label_text):
    raw = str(label_text).strip().lower()
    if not raw:
        return ""

    raw = re.sub(r'\s+', ' ', raw)
    raw = re.sub(r'(?i)\bdriver\s*\d+\b', 'driver', raw)
    raw = re.sub(r'(?i)\b\d+\s*driver\b', 'driver', raw)
    raw = re.sub(r'\d+', '', raw).strip()
    compact_raw = _compact_label_token(raw)
    if not compact_raw:
        return ""

    # Fast path: exact compact match.
    for canonical, aliases in _FIELD_LABEL_ALIASES.items():
        for alias in aliases:
            if compact_raw == _compact_label_token(alias):
                return canonical

    # Fuzzy path: tolerate small typos on short label tokens.
    best_label = ""
    best_score = None
    for canonical, aliases in _FIELD_LABEL_ALIASES.items():
        for alias in aliases:
            compact_alias = _compact_label_token(alias)
            if not compact_alias:
                continue
            max_dist = 1 if len(compact_alias) <= 5 else 2
            dist = _levenshtein_limited(compact_raw, compact_alias, max_dist=max_dist)
            if dist is None:
                continue
            score = (dist, abs(len(compact_raw) - len(compact_alias)))
            if best_score is None or score < best_score:
                best_score = score
                best_label = canonical
    return best_label

def normalize_field_labels_in_text(text):
    if pd.isna(text) or text is None:
        return ""
    text_str = str(text)
    if not text_str.strip():
        return text_str

    normalized_lines = []
    for raw_line in text_str.splitlines():
        m = re.match(r'^(\s*)([^:\n\r]{2,40}?)(\s*[:=]\s*)(.*)$', raw_line)
        if not m:
            normalized_lines.append(raw_line)
            continue
        lead, label, sep, value = m.groups()
        canonical = _normalize_field_label_token(label)
        if canonical:
            # Pertahankan indeks Driver 1/2 agar logika pair tetap berjalan.
            if canonical == "driver":
                idx = ""
                m_idx = re.search(r'(?i)(?:driver|dr\w*)\s*([12])|([12])\s*(?:driver|dr\w*)', label)
                if m_idx:
                    idx = m_idx.group(1) or m_idx.group(2) or ""
                if idx:
                    canonical = f"driver {idx}"
            normalized_lines.append(f"{lead}{canonical}{sep}{value}")
        else:
            normalized_lines.append(raw_line)
    return "\n".join(normalized_lines)

def extract_time_format(time_str):
    time_str = str(time_str).strip().upper()
    if "SEGERA" in time_str:
        return ("SEGERA", "segera")
    # Toleransi separator jam: ":" "." ";"
    m = re.search(r'(\d{1,2})[:\.;](\d{2})', time_str)
    if m:
        hour = int(m.group(1))
        minute = m.group(2)
        return (f"{hour:02d}:{minute}", "HH:MM")
    m = re.search(r'^(\d{1,2})$', time_str.strip())
    if m:
        hour = int(m.group(1))
        return (f"{hour:02d}:00", "HH")
    return (time_str, "unknown")

def auto_format_chat_input(text):
    if not text: return ""
    # Hilangkan BOM jika ada agar header pertama tetap terbaca.
    text = str(text).lstrip("\ufeff").replace("\ufeff", "")
    text = normalize_field_labels_in_text(text)
    wa_pattern = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
    chunks = re.split(wa_pattern, text)
    valid_text = ""
    for chunk in chunks:
        if not chunk.strip(): continue
        chunk_lower = chunk.lower()
        if "contoh chat" in chunk_lower or "latih ai" in chunk_lower or "minta contoh" in chunk_lower:
            continue
        valid_text += chunk

    if not valid_text.strip(): valid_text = text
    lines = valid_text.split('\n')
    formatted_lines = []

    pattern_with_date = r"(?i)(Waktu loading\s*:\s*)(.*?)(\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\s+\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})"
    date_header_pattern = r"(?:REQUEST|ONCALL|TAMBAHAN).*?(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    waktu_loading_standalone = r"(?i)Waktu\s+loading\s*:\s*(.+?)(?=\n|$)"

    current_global_date = ""
    current_block_date = ""
    # Tanggal pesan WhatsApp hanya dipakai untuk mengenali metadata, bukan sebagai tanggal order.
    current_wa_message_date = ""
    active_request_has_header_date = False
    active_request_wa_date = ""
    active_request_fallback_line_indexes = []
    active_request_explicit_dates = []

    month_map = {
        "JAN": 1, "JANUARI": 1,
        "FEB": 2, "FEBRUARI": 2, "FEBUARI": 2,
        "MAR": 3, "MARET": 3,
        "APR": 4, "APRIL": 4,
        "MEI": 5,
        "JUN": 6, "JUNI": 6,
        "JUL": 7, "JULI": 7,
        "AUG": 8, "AGUSTUS": 8, "AGUS": 8,
        "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
        "OKT": 10, "OKTOBER": 10, "OCT": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DES": 12, "DESEMBER": 12, "DEC": 12,
    }

    def _parse_date_triplet(date_text):
        if not date_text:
            return None
        s = str(date_text).strip().upper()

        m_num = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', s)
        if m_num:
            day = int(m_num.group(1))
            month = int(m_num.group(2))
            year = int(m_num.group(3))
            if year < 100:
                year += 2000
            if 1 <= day <= 31 and 1 <= month <= 12:
                return day, month, year

        m_named = re.search(r'\b(\d{1,2})\s+([A-Z]+)\s+(\d{2,4})\b', s)
        if m_named:
            day = int(m_named.group(1))
            month = month_map.get(m_named.group(2), 0)
            year = int(m_named.group(3))
            if year < 100:
                year += 2000
            if month and 1 <= day <= 31:
                return day, month, year

        return None

    def _finalize_active_request_dates():
        nonlocal active_request_fallback_line_indexes
        if active_request_has_header_date:
            return
        if not active_request_wa_date or not active_request_fallback_line_indexes:
            return

        wa_parts = _parse_date_triplet(active_request_wa_date)
        if not wa_parts:
            return

        ref_parts = None
        for dt in active_request_explicit_dates:
            parsed = _parse_date_triplet(dt)
            if parsed:
                ref_parts = parsed
                break
        if not ref_parts:
            return

        wa_day, wa_month, wa_year = wa_parts
        _, ref_month, ref_year = ref_parts
        if wa_month == ref_month and wa_year == ref_year:
            return

        corrected_date = f"{wa_day}/{ref_month:02d}/{ref_year:04d}"
        for idx_line in active_request_fallback_line_indexes:
            if 0 <= idx_line < len(formatted_lines):
                formatted_lines[idx_line] = re.sub(
                    r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b)\s*$',
                    corrected_date,
                    formatted_lines[idx_line],
                )

    for line in lines:
        header_timestamp_pattern = r'\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
        wa_prefix_pattern = (
            r'^\s*\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
            r'\s*[^:\n\r]*:\s*'
        )
        wa_prefix_match = re.search(wa_prefix_pattern, line)
        timestamp_match = wa_prefix_match or re.search(header_timestamp_pattern, line)
        if timestamp_match:
            current_wa_message_date = timestamp_match.group(2).strip()
            # Reset konteks tanggal per pesan baru agar tidak carry-over ke pesan berikutnya.
            current_global_date = ""
            current_block_date = ""
            if wa_prefix_match:
                line = re.sub(wa_prefix_pattern, "", line, count=1)
            else:
                line = re.sub(header_timestamp_pattern, "", line).strip()

        is_request_header = re.search(r"(?i)(?:REQUEST|ONCALL|TAMBAHAN)", line)
        if is_request_header:
            _finalize_active_request_dates()
            header_match = re.search(date_header_pattern, line, re.IGNORECASE)
            if header_match:
                current_global_date = header_match.group(1)
                current_block_date = current_global_date
            else:
                current_global_date = ""
                current_block_date = ""
            active_request_has_header_date = bool(header_match)
            active_request_wa_date = ""
            active_request_fallback_line_indexes = []
            active_request_explicit_dates = []
            formatted_lines.append(line)
            continue

        time_date_slash_line = re.search(
            r'(?i)Waktu\s*loading\s*:\s*\d{1,2}[:.]\d{2}\s*[\\/]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})',
            line
        )
        match = None if time_date_slash_line else re.search(pattern_with_date, line)
        # Guard: jangan anggap "Waktu loading : <DATE_ONLY>" sebagai pola "jam + tanggal".
        if match and not str(match.group(2) or "").strip():
            match = None
        if match:
            prefix = match.group(1)
            jam = match.group(2).strip()
            tgl = match.group(3).strip()
            jam_clean, _ = extract_time_format(jam)
            formatted_lines.append(f"\nREQUEST ORDER KHUSUS {tgl}")
            formatted_lines.append(f"{prefix}{jam_clean}")
            current_global_date = tgl
            current_block_date = tgl
            active_request_explicit_dates.append(tgl)
            continue

        standalone_match = re.search(waktu_loading_standalone, line, re.IGNORECASE)
        if standalone_match:
            jam_raw = standalone_match.group(1).strip()
            time_date_slash = re.search(
                r'(?i)^\s*(\d{1,2}[:.]\d{2})\s*[\\/]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})',
                jam_raw
            )
            if time_date_slash:
                jam_part = time_date_slash.group(1).strip()
                tgl_part = time_date_slash.group(2).strip()
                jam_clean, _ = extract_time_format(jam_part)
                formatted_lines.append(f"Waktu loading : {jam_clean} {tgl_part}")
                current_global_date = tgl_part
                current_block_date = tgl_part
                active_request_explicit_dates.append(tgl_part)
            else:
                date_in_value = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', jam_raw)
                if not date_in_value:
                    date_in_value = re.search(r'(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})', jam_raw)
                if date_in_value:
                    jam_part = jam_raw[:date_in_value.start()].strip()
                    jam_part = re.sub(r'[\\/\\-]+\\s*$', '', jam_part).strip()
                    tgl_part = date_in_value.group(1)
                    active_request_explicit_dates.append(tgl_part)
                    # Jika value hanya tanggal (tanpa jam/SEGERA), jangan ubah global date context.
                    if jam_part:
                        jam_clean, _ = extract_time_format(jam_part)
                        formatted_lines.append(f"Waktu loading : {jam_clean} {tgl_part}")
                        current_global_date = tgl_part
                        current_block_date = tgl_part
                    else:
                        formatted_lines.append(f"Waktu loading : {tgl_part}")
                else:
                    jam_clean, _ = extract_time_format(jam_raw)
                    if current_global_date:
                        formatted_lines.append(f"Waktu loading : {jam_clean} {current_global_date}")
                        if (
                            active_request_wa_date
                            and not active_request_has_header_date
                            and current_global_date == active_request_wa_date
                        ):
                            active_request_fallback_line_indexes.append(len(formatted_lines) - 1)
                    else:
                        formatted_lines.append(f"Waktu loading : {jam_clean}")
            continue

        formatted_lines.append(line)

    _finalize_active_request_dates()
    return "\n".join(formatted_lines)

def extract_plate_aggressive(text):
    if pd.isna(text): return ""
    text = str(text).upper()
    match = re.search(r"\b([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})\b", text)
    if match: return match.group(1)
    return ""

def clean_plate_value(plate):
    if plate is None:
        return ""
    s = str(plate).strip().upper()
    if not s or s.lower() in ['none', 'nan', 'nat']:
        return ""
    s = re.sub(r'[^A-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if re.fullmatch(r'0+', s):
        return ""
    if not re.search(r'[A-Z]', s):
        return ""
    if not re.search(r'\d', s):
        return ""
    return s

def normalize_phone_number(phone):
    if pd.isna(phone) or not str(phone).strip(): return ""
    phone_digits = re.sub(r'\D', '', str(phone))
    if not phone_digits: return ""
    if phone_digits.startswith('62'): phone_digits = '0' + phone_digits[2:]
    return phone_digits

def extract_phone_numbers_from_text(original_text):
    if pd.isna(original_text) or not str(original_text).strip():
        return []
    text = normalize_field_labels_in_text(original_text)
    labels = [
        r'no\.?\s*hp',
        r'no\.?\s*telp',
        r'no\.?\s*tlp',
        r'kontak',
        r'\bhp\b',
    ]
    numbers = []
    for label in labels:
        for m in re.finditer(label, text, re.IGNORECASE):
            tail = text[m.end():m.end()+60]
            mnum = re.search(r'([+0-9][0-9\s\-]{6,})', tail)
            if mnum:
                num = normalize_phone_number(mnum.group(1))
                if num and num not in numbers:
                    numbers.append(num)
    return numbers

def extract_phone_pair_from_text(original_text):
    nums = extract_phone_numbers_from_text(original_text)
    if len(nums) >= 2:
        return (nums[0], nums[1])
    return ("", "")

def normalize_origin(text):
    if pd.isna(text) or not str(text).strip(): return ""
    origin = str(text).upper().strip()
    if origin.lower() in ['none', 'nan', 'nat']: return ""
    origin = re.sub(r'[â€“â€”âˆ’]', '-', origin)
    origin = origin.replace('*', ' ')
    origin = origin.replace('/', ' ')
    origin = re.sub(r'\s*-\s*', ' ', origin)
    origin = origin.replace(',', ' ')
    origin = re.sub(r'\s+', ' ', origin).strip(" -")
    return origin

def normalize_route(text):
    if pd.isna(text) or not str(text).strip(): return ""
    text_str = str(text).strip()
    if text_str.lower() in ['none', 'nan', 'nat']: return ""
    route = text_str.upper()
    route = re.sub(r'[â€“â€”âˆ’]', '-', route)
    route = route.replace('*', ' ')
    route = re.sub(r'[^\w\s,/-]', ' ', route)
    route = re.sub(r'\s+', ' ', route).strip(" ,-")
    if not re.search(r'[A-Z]', route):
        return ""

    # Route jadi format "A, B" hanya jika input memang punya separator route.
    if '-' in route or ',' in route or '/' in route:
        normalized_sep = re.sub(r'\s*[/,-]\s*', ',', route)
        parts = [p.strip() for p in normalized_sep.split(',') if p.strip()]
        if len(parts) >= 2:
            return ", ".join(parts)
        if len(parts) == 1:
            return parts[0]
        return ""

    # Tujuan tunggal tanpa separator tetap apa adanya (tanpa koma).
    if re.fullmatch(r'[A-Z]{6}', route):
        return f"{route[:3]}, {route[3:]}"
    if re.fullmatch(r'[A-Z]{3}\s+[A-Z]{3}', route):
        parts = route.split()
        return f"{parts[0]}, {parts[1]}"
    return route

def extract_route_from_text(text):
    if pd.isna(text) or not str(text).strip(): return ""
    norm_text = normalize_field_labels_in_text(text)
    m = re.search(r'(?im)^\s*Rute\s*(?:/|\s+)\s*(?:tujuan|tuj(?:u(?:an)?)?)\s*:\s*([^\n\r]+)', str(norm_text))
    return m.group(1).strip() if m else ""

def extract_origin_from_text(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    norm_text = normalize_field_labels_in_text(text)
    m = re.search(r'(?im)^\s*Lokasi\s*:\s*([^\n\r]+)', str(norm_text))
    return m.group(1).strip() if m else ""

def extract_ro_date_from_text(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    text_str = str(text)
    header_pattern = r'(?im)^\s*.*(?:REQUEST|ONCALL|TAMBAHAN|ORDER|UNIT\s+ON\s+CALL|ON\s+CALL|TGL)\b.*$'
    month_pattern = (
        r'(?:JANUARI|JAN|FEBRUARI|FEBUARI|FEBRUARY|FEBUARY|FEB|MARET|MAR|APRIL|APR|MEI|'
        r'JUNI|JUN|JULI|JUL|AGUSTUS|AGUS|AGUST|AUGUST|AUG|SEPTEMBER|SEPT|SEP|'
        r'OKTOBER|OKT|OCTOBER|OCT|NOVEMBER|NOV|DESEMBER|DES|DECEMBER|DEC)'
    )
    date_pattern = rf'(?i)(\d{{1,2}}\s+{month_pattern}(?:\s+\d{{2,4}})?|\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?)'

    lines = text_str.splitlines()
    for idx, line in enumerate(lines):
        if not re.search(header_pattern, line):
            continue
        # Cek tanggal pada baris header
        m_inline = re.search(date_pattern, line)
        if m_inline:
            return m_inline.group(1).strip()
        # Jika tanggal ada di baris berikutnya (header multi-line)
        for look_ahead in range(1, 3):
            if idx + look_ahead < len(lines):
                next_line = lines[idx + look_ahead]
                # Jangan ambil RO date dari baris Waktu loading.
                if re.search(r'(?i)^\s*waktu\s*loading\s*:', next_line):
                    continue
                m_next = re.search(date_pattern, next_line)
                if m_next:
                    return m_next.group(1).strip()
        break
    return ""

def extract_unit_qty(text, unit_qty_raw=""):
    text_str = str(text) if text is not None else ""
    raw = str(unit_qty_raw) if unit_qty_raw is not None else ""
    # Prioritaskan pola eksplisit "X unit" dari teks asli
    m = re.search(r'(?i)\b(\d{1,3})\s*unit\b', text_str)
    if m:
        try:
            return int(m.group(1))
        except:
            pass
    if not raw or raw.lower() in ['none', 'nan', 'nat']:
        return None
    # Jika raw mengandung CBM/kapasitas, abaikan angka kapasitas sebagai qty
    if re.search(r'(?i)\bcbm\b', raw):
        m_raw = re.search(r'(?i)\b(\d{1,3})\s*unit\b', raw)
        if m_raw:
            try:
                return int(m_raw.group(1))
            except:
                return None
        return None
    m_num = re.search(r'^\s*(\d{1,3})\s*$', raw)
    if m_num:
        try:
            return int(m_num.group(1))
        except:
            return None
    m_unit = re.search(r'(?i)\b(\d{1,3})\s*unit\b', raw)
    if m_unit:
        try:
            return int(m_unit.group(1))
        except:
            return None
    return None

def extract_unit_type_from_text(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    # Ambil tipe unit dari baris "X unit ..."
    m = re.search(r'(?im)^\s*\d+\s*unit\s+([^\n\r]+)', str(text))
    if m:
        return normalize_unit_type(m.group(1))
    return ""

def extract_loading_candidates(text):
    if pd.isna(text) or not str(text).strip():
        return []
    text = normalize_field_labels_in_text(text)
    candidates = []
    date_token = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4}'
    date_pattern = rf'\b({date_token})\b'
    khusus_pattern = rf'(?i)REQUEST\s+ORDER\s+KHUSUS\s+({date_token})'
    for match in re.finditer(r'(?im)^\s*Waktu\s*loading\s*:[ \t]*([^\n\r]+)', str(text)):
        val = str(match.group(1)).strip()
        if not val:
            continue
        pos = match.start()
        val_upper = val.upper()
        has_segera = "SEGERA" in val_upper
        date_part = ""
        # Prioritas: format inline "HH:MM/DATE" atau "HH.MM / DATE"
        inline_slash = re.search(
            r'(?i)^\s*\d{1,2}[:\.;]\d{2}\s*[\\/]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})',
            val
        )
        if inline_slash:
            date_part = inline_slash.group(1).strip()
        for m in re.finditer(date_pattern, val):
            cand = m.group(1).strip()
            if re.search(r'[/-]', cand):
                parts = re.split(r'[/-]', cand)
                if len(parts) >= 3:
                    try:
                        day = int(parts[0]); month = int(parts[1])
                        if 1 <= day <= 31 and 1 <= month <= 12:
                            date_part = cand
                            break
                    except:
                        pass
            else:
                # Month name format dianggap valid
                date_part = cand
                break
        if not date_part:
            prefix_text = str(text)[:pos]
            khusus_matches = list(re.finditer(khusus_pattern, prefix_text))
            if khusus_matches:
                date_part = khusus_matches[-1].group(1).strip()
        if has_segera:
            time_part = "SEGERA"
        else:
            time_part, _ = extract_time_format(val_upper)
            if time_part == val_upper and not re.search(r'\d', val_upper):
                time_part = ""
        candidates.append({"time": time_part, "date": date_part, "segera": has_segera, "raw": val, "pos": pos})
    return candidates

def extract_loading_details(text):
    if pd.isna(text) or not str(text).strip():
        return []
    text_str = normalize_field_labels_in_text(text)
    details = []
    loading_matches = list(re.finditer(r'(?im)^\s*Waktu\s*loading\s*:[ \t]*([^\n\r]+)', text_str))
    for idx, m in enumerate(loading_matches):
        val = str(m.group(1)).strip()
        if not val:
            continue
        start = m.start()
        end = loading_matches[idx + 1].start() if (idx + 1) < len(loading_matches) else len(text_str)
        section = text_str[start:end]

        base = extract_loading_candidates(f"Waktu loading : {val}")
        if base:
            time_part = str(base[0].get("time", "")).strip()
            date_part = str(base[0].get("date", "")).strip()
            has_segera = bool(base[0].get("segera"))
        else:
            time_part, _ = extract_time_format(val)
            date_part = ""
            has_segera = "SEGERA" in val.upper()

        driver = ""
        plate = ""
        phone = ""

        driver_match = re.search(
            r'(?im)^[ \t]*(?:driver|pengemudi)(?:[ \t]*\d+)?[ \t]*[:.]?[ \t]*([^\n\r]*)',
            section
        )
        if driver_match:
            driver = clean_driver_name(driver_match.group(1))

        plate_match = re.search(
            r'(?im)^[ \t]*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)[ \t]*[:.]?[ \t]*([^\n\r]*)',
            section
        )
        if plate_match:
            plate = clean_plate_value(plate_match.group(1))

        phone_match = re.search(r'(?im)^[ \t]*(?:no\.?\s*hp|hp|no\.?\s*telp|no\.?\s*tlp|kontak)[ \t]*[:.]?[ \t]*([^\n\r]*)', section)
        if phone_match:
            phone = normalize_phone_number(phone_match.group(1))

        details.append({
            "time": time_part,
            "date": date_part,
            "segera": has_segera,
            "driver": driver,
            "plate": plate,
            "phone": phone,
            "raw": val,
            "pos": start,
        })
    return details

def normalize_unit_type(unit_type):
    if pd.isna(unit_type) or not str(unit_type).strip(): return ""
    unit = str(unit_type).upper().strip()
    if unit.lower() in ['none', 'nan', 'nat']: return ""
    unit = re.sub(r'[^A-Z0-9\s]', ' ', unit)
    unit = re.sub(r'\s+', ' ', unit).strip()
    for token in unit.split():
        token_clean = re.sub(r'\d+', '', token)
        if token in ['CBM', 'M3', 'M^3'] or token_clean in ['CBM', 'M']:
            continue
        if token_clean:
            return token_clean
    return ""

def clean_driver_name(name):
    if not name or pd.isna(name) or str(name).lower() == 'none': return ""
    clean_name = str(name).strip().title()
    for bad_word in DRIVER_BLACKLIST:
        if bad_word.lower() in clean_name.lower(): return ""
    return clean_name

def _clean_driver_fragment(text):
    if not text:
        return ""
    # Potong jika ada field lain di baris yang sama
    text = re.split(r'\b(no\.?\s*hp|no\.?\s*pol|nopol|hp|telp|phone)\b', text, flags=re.IGNORECASE)[0]
    text = re.sub(r'[^A-Za-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return clean_driver_name(text)

def extract_driver_pair_from_text(original_text):
    if not original_text:
        return ("", "")
    original_text = normalize_field_labels_in_text(original_text)
    patterns = [
        r'(?:driver|pengemudi)\s*\.?\s*1\s*[:=]?\s*([^\n\r]+)',
        r'(?:driver|pengemudi)\s*\.?\s*2\s*[:=]?\s*([^\n\r]+)'
    ]
    m1 = re.search(patterns[0], original_text, re.IGNORECASE)
    m2 = re.search(patterns[1], original_text, re.IGNORECASE)
    d1 = _clean_driver_fragment(m1.group(1)) if m1 else ""
    d2 = _clean_driver_fragment(m2.group(1)) if m2 else ""
    return (d1, d2)

def apply_driver_pair_from_text(df_final):
    if df_final is None or df_final.empty:
        return df_final
    if 'Original_Text' not in df_final.columns or 'DRIVER' not in df_final.columns:
        return df_final
    df = df_final.copy()
    for idx, row in df.iterrows():
        original_text = str(row.get('Original_Text', ''))
        d1, d2 = extract_driver_pair_from_text(original_text)
        if not d1 or not d2:
            continue
        if d1.lower() == d2.lower():
            combined = d1
        else:
            combined = f"{d1} & {d2}"
        current = str(row.get('DRIVER', '')).strip()
        if not current:
            df.at[idx, 'DRIVER'] = combined
            continue
        current_norm = clean_driver_name(current).lower()
        # Normalisasi label seperti "driver 1 : nama" atau "1 : nama"
        # agar tetap bisa dikenali sebagai driver tunggal dari pasangan.
        current_norm = re.sub(
            r'^\s*(?:(?:driver|pengemudi)\s*\.?\s*)?\d+\s*[:=\-]?\s*',
            '',
            current_norm,
            flags=re.IGNORECASE,
        ).strip()
        if current_norm in [d1.lower(), d2.lower()] or '&' in current:
            df.at[idx, 'DRIVER'] = combined
    return df

def apply_phone_pair_from_text(df_final):
    if df_final is None or df_final.empty:
        return df_final
    if 'Original_Text' not in df_final.columns or 'PHONE' not in df_final.columns:
        return df_final
    df = df_final.copy()
    for idx, row in df.iterrows():
        original_text = str(row.get('Original_Text', ''))
        d1, d2 = extract_driver_pair_from_text(original_text)
        if not d1 or not d2:
            continue
        p1, p2 = extract_phone_pair_from_text(original_text)
        if not p1 or not p2:
            continue
        combined = p1 if p1 == p2 else f"{p1} & {p2}"
        current = str(row.get('PHONE', '')).strip()
        if not current:
            df.at[idx, 'PHONE'] = combined
            continue
        if '&' in current:
            continue
        if current in [p1, p2] or current in [f"{p1}{p2}", f"{p2}{p1}"]:
            df.at[idx, 'PHONE'] = combined
    return df

def sanitize_row_data(row):
    d = str(row.get('DATE', '')).strip()
    t = str(row.get('TIME', '')).strip()
    orig_text = str(row.get('Original_Text', '')).strip()
    drv = str(row.get('DRIVER', '')).strip()
    ro_date = str(row.get('RO_DATE', '')).strip() if 'RO_DATE' in row else ""
    date_from_time = ""
    time_from_value = ""
    date_from_time_source = False

    if d.lower() in ['none', 'nan', 'nat']: d = ""
    if t.lower() in ['none', 'nan', 'nat']: t = ""
    if ro_date.lower() in ['none', 'nan', 'nat']: ro_date = ""

    if not clean_driver_name(drv):
        d1, d2 = extract_driver_pair_from_text(orig_text)
        if d1 and d2:
            row['DRIVER'] = f"{d1} & {d2}" if d1.lower() != d2.lower() else d1
            drv = row['DRIVER']

    has_segera = False
    if "segera" in t.lower(): has_segera = True
    elif "segera" in d.lower(): has_segera = True; d = ""
    elif "segera" in drv.lower(): has_segera = True
    elif "segera" in orig_text.lower(): has_segera = True

    if has_segera:
        t = "SEGERA"
    else:
        # Jika TIME berisi tanggal (contoh: "02.00/10-02-26" atau "06:00/06 Mar 26"),
        # pindahkan tanggal ke DATE sebelum normalisasi TIME.
        if t and not d:
            m_time_date = re.search(r'(?i)^\s*(\d{1,2}[:.]\d{2})\s*[\\/]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})', t)
            if m_time_date:
                time_from_value = m_time_date.group(1).strip()
                date_from_time = m_time_date.group(2).strip()
                date_from_time_source = True
                t = time_from_value
                d = date_from_time
        time_in_date_pattern = r'^(\d{1,2}:\d{2})\s+(.+)$'
        time_in_date_match = re.search(time_in_date_pattern, d)
        if time_in_date_match:
            potential_time = time_in_date_match.group(1)
            remaining_date = time_in_date_match.group(2)
            if not date_from_time_source:
                date_from_time = remaining_date.strip()
                date_from_time_source = True
            if not t or t in ["SEGERA", ""]:
                t = potential_time
                time_from_value = potential_time
            d = remaining_date.strip()

        is_time_misplaced = re.match(r'^(\d{1,2}|\d{1,2}[:.]\d{2})$', d)
        if is_time_misplaced:
            if not t or t in ["SEGERA", ""]:
                t = d
            d = ""

        if t and t != "SEGERA":
            t = re.sub(r'\s+', '', t)
            t = t.replace(".", ":").replace("*", "").upper()
            m = re.search(r'^(\d{1,2}):(\d{2})', t)
            if m:
                hour = int(m.group(1))
                minute = m.group(2)
                t = f"{hour:02d}:{minute}"
            elif re.match(r'^\d{1,2}$', t):
                hour = int(t.split()[0])
                t = f"{hour:02d}:00"
            if date_from_time_source and not time_from_value:
                time_from_value = t

    if not t or t == "":
        fallback_match = re.search(r"(?i)Waktu\s+loading\s*:\s*([0-9]{1,2}\s*:\s*[0-9]{2}|[0-9]{1,2}|SEGERA)", orig_text)
        if fallback_match:
            waktu_fallback = fallback_match.group(1).strip().upper()
            waktu_fallback = re.sub(r'\s+', '', waktu_fallback)
            if "SEGERA" in waktu_fallback:
                t = "SEGERA"
            else:
                m = re.search(r'^(\d{1,2}):(\d{2})', waktu_fallback)
                if m:
                    hour = int(m.group(1))
                    minute = m.group(2)
                    t = f"{hour:02d}:{minute}"
                elif re.match(r'^\d{1,2}$', waktu_fallback):
                    hour = int(waktu_fallback)
                    t = f"{hour:02d}:00"
                else:
                    t = waktu_fallback

    if 'PHONE' in row:
        phone_from_pair = False
        d1, d2 = extract_driver_pair_from_text(orig_text)
        if d1 and d2:
            p1, p2 = extract_phone_pair_from_text(orig_text)
            if p1 and p2:
                row['PHONE'] = p1 if p1 == p2 else f"{p1} & {p2}"
                phone_from_pair = True
        if not phone_from_pair:
            raw_phone = str(row.get('PHONE', '')).strip()
            if raw_phone and raw_phone.lower() not in ['none', 'nan', 'nat', '']:
                # Jika ada lebih dari satu nomor dalam satu field, gabungkan dengan "&"
                nums = [normalize_phone_number(n) for n in re.findall(r'\d{6,}', raw_phone)]
                nums = [n for n in nums if n]
                if len(nums) >= 2:
                    row['PHONE'] = f"{nums[0]} & {nums[1]}"
                else:
                    row['PHONE'] = normalize_phone_number(raw_phone)
            else:
                row['PHONE'] = ""
    
    if 'ORIGIN' in row:
        raw_origin = str(row.get('ORIGIN', '')).strip()
        if raw_origin and raw_origin.lower() not in ['none', 'nan', 'nat', '']:
            row['ORIGIN'] = normalize_origin(raw_origin)
        else:
            row['ORIGIN'] = ""

    if 'DESTINATION' in row:
        raw_destination = str(row.get('DESTINATION', '')).strip()
        if raw_destination and raw_destination.lower() not in ['none', 'nan', 'nat', '']:
            row['DESTINATION'] = normalize_route(raw_destination)
        else:
            row['DESTINATION'] = ""

    route_from_text = extract_route_from_text(orig_text)
    if route_from_text:
        row['DESTINATION'] = normalize_route(route_from_text)

    origin_from_text = extract_origin_from_text(orig_text)
    if origin_from_text:
        row['ORIGIN'] = normalize_origin(origin_from_text)

    if 'UNIT_TYPE' in row:
        raw_unit = str(row.get('UNIT_TYPE', '')).strip()
        if raw_unit and raw_unit.lower() not in ['none', 'nan', 'nat', '']:
            row['UNIT_TYPE'] = normalize_unit_type(raw_unit)
        else:
            row['UNIT_TYPE'] = ""
        if not row.get('UNIT_TYPE'):
            unit_from_text = extract_unit_type_from_text(str(row.get('Original_Text', '')).strip())
            if unit_from_text:
                row['UNIT_TYPE'] = unit_from_text

    ro_from_text = extract_ro_date_from_text(orig_text)
    if ro_from_text:
        ro_date = ro_from_text
    row['RO_DATE'] = ro_date

    # Aturan Tgl Muat:
    # - Jika Waktu loading SEGERA atau tidak ada, kosongkan Tgl Muat.
    # - Jika Waktu loading punya tanggal spesifik, itu jadi Tgl Muat.
    # - Jika Waktu loading hanya jam, Tgl Muat mengikuti Tgl RO.
    loading_candidates = extract_loading_candidates(orig_text)
    muat_date = ""
    if loading_candidates:
        chosen = None
        if t:
            matching = [cand for cand in loading_candidates if cand.get("time") and cand.get("time").upper() == t.upper()]
            if len(matching) == 1:
                chosen = matching[0]
            elif len(matching) > 1:
                anchor_pos = -1
                search_targets = []
                if drv:
                    search_targets.append(drv)
                plate_val = str(row.get('PLATE', '')).strip()
                if plate_val:
                    search_targets.append(plate_val)
                for target in search_targets:
                    try:
                        m_anchor = re.search(re.escape(target), orig_text, re.IGNORECASE)
                    except re.error:
                        m_anchor = None
                    if m_anchor:
                        anchor_pos = m_anchor.start()
                        break
                if anchor_pos >= 0:
                    chosen = min(matching, key=lambda c: abs(c.get("pos", 0) - anchor_pos))
                else:
                    chosen = matching[0]
        if chosen is None:
            chosen = loading_candidates[0]

        if chosen.get("segera"):
            # Waktu loading SEGERA -> Tgl Muat = Tgl RO, Jam kosong
            muat_date = ro_date
            t = ""
        elif chosen.get("date"):
            muat_date = chosen.get("date")
            t = chosen.get("time") or ""
        else:
            muat_date = ro_date if ro_date else ""
            t = chosen.get("time") or ""
    else:
        # Tidak ada Waktu loading sama sekali -> Tgl Muat kosong, Jam kosong
        muat_date = ""
        if date_from_time_source:
            muat_date = date_from_time
            if not t and time_from_value:
                t = time_from_value
        else:
            t = ""

    if not muat_date and date_from_time_source:
        muat_date = date_from_time
        if not t and time_from_value:
            t = time_from_value

    row['DATE'] = muat_date
    row['TIME'] = t
    return row

def normalize_header_context_fields(row):
    if row is None:
        return row
    row = row.copy()

    if 'ORIGIN' in row:
        raw_origin = str(row.get('ORIGIN', '')).strip()
        if raw_origin and raw_origin.lower() not in ['none', 'nan', 'nat', '']:
            row['ORIGIN'] = normalize_origin(raw_origin)
        else:
            row['ORIGIN'] = ""

    if 'DESTINATION' in row:
        raw_destination = str(row.get('DESTINATION', '')).strip()
        if raw_destination and raw_destination.lower() not in ['none', 'nan', 'nat', '']:
            row['DESTINATION'] = normalize_route(raw_destination)
        else:
            row['DESTINATION'] = ""

    route_from_text = extract_route_from_text(str(row.get('Original_Text', '')).strip())
    if route_from_text:
        row['DESTINATION'] = normalize_route(route_from_text)

    origin_from_text = extract_origin_from_text(str(row.get('Original_Text', '')).strip())
    if origin_from_text:
        row['ORIGIN'] = normalize_origin(origin_from_text)

    if 'UNIT_TYPE' in row:
        raw_unit = str(row.get('UNIT_TYPE', '')).strip()
        if raw_unit and raw_unit.lower() not in ['none', 'nan', 'nat', '']:
            row['UNIT_TYPE'] = normalize_unit_type(raw_unit)
        else:
            row['UNIT_TYPE'] = ""

    return row

def repair_headers(df):
    if df is None or df.empty: return df
    df = df.copy()

    # Hardening schema agar tidak pernah KeyError saat model tidak mengeluarkan kolom tertentu.
    for col in ['DESTINATION', 'ORIGIN', 'UNIT_TYPE', 'UNIT_QTY', 'RO_DATE']:
        if col not in df.columns:
            df[col] = pd.NA
    if 'Original_Text' not in df.columns:
        df['Original_Text'] = ""

    for col in ['DESTINATION', 'ORIGIN', 'UNIT_TYPE']:
        df[col] = df[col].replace(['', 'None', 'NONE', 'nan', 'nan '], pd.NA)

    for i in range(len(df)):
        orig_text = str(df.at[i, 'Original_Text']) if 'Original_Text' in df.columns else ""
        origin_from_text = extract_origin_from_text(orig_text)
        route_from_text = extract_route_from_text(orig_text)

        if pd.notna(df.at[i, 'ORIGIN']):
            df.at[i, 'ORIGIN'] = normalize_origin(df.at[i, 'ORIGIN'])
        if pd.notna(df.at[i, 'DESTINATION']):
            df.at[i, 'DESTINATION'] = normalize_route(df.at[i, 'DESTINATION'])
        if pd.notna(df.at[i, 'UNIT_TYPE']):
            df.at[i, 'UNIT_TYPE'] = normalize_unit_type(df.at[i, 'UNIT_TYPE'])

        if pd.isna(df.at[i, 'UNIT_TYPE']) or str(df.at[i, 'UNIT_TYPE']).strip() == "":
            unit_from_text = extract_unit_type_from_text(orig_text)
            if unit_from_text:
                df.at[i, 'UNIT_TYPE'] = unit_from_text

        if origin_from_text:
            origin_norm = normalize_origin(origin_from_text)
            # Lokasi dari teks asli jadi sumber utama Pickup.
            df.at[i, 'ORIGIN'] = origin_norm
            # Jika model salah label lokasi ke DESTINATION pada baris tanpa route,
            # kosongkan agar bisa diwarisi dari baris rute berikutnya.
            if not route_from_text:
                dest_val = str(df.at[i, 'DESTINATION']).strip() if pd.notna(df.at[i, 'DESTINATION']) else ""
                if dest_val and normalize_origin(dest_val) == origin_norm:
                    df.at[i, 'DESTINATION'] = pd.NA
        if route_from_text:
            route_norm = normalize_route(route_from_text)
            # Rute dari teks asli jadi sumber utama Tujuan.
            df.at[i, 'DESTINATION'] = route_norm

        # Jika driver kosong tapi ada Driver 1 & Driver 2 di teks, gabungkan.
        drv_val = str(df.at[i, 'DRIVER']).strip() if 'DRIVER' in df.columns else ""
        if not clean_driver_name(drv_val):
            d1, d2 = extract_driver_pair_from_text(orig_text)
            if d1 and d2:
                df.at[i, 'DRIVER'] = f"{d1} & {d2}" if d1.lower() != d2.lower() else d1
        if 'PHONE' in df.columns:
            cur_phone = str(df.at[i, 'PHONE']).strip() if pd.notna(df.at[i, 'PHONE']) else ""
            d1, d2 = extract_driver_pair_from_text(orig_text)
            if d1 and d2:
                p1, p2 = extract_phone_pair_from_text(orig_text)
                if p1 and p2:
                    combined = p1 if p1 == p2 else f"{p1} & {p2}"
                    if not cur_phone or (('&' not in cur_phone) and (cur_phone in [p1, p2])):
                        df.at[i, 'PHONE'] = combined

        ro_from_text = extract_ro_date_from_text(orig_text)
        if ro_from_text:
            df.at[i, 'RO_DATE'] = ro_from_text

        qty_val = str(df.at[i, 'UNIT_QTY'])
        qty_num = extract_unit_qty(orig_text, qty_val)
        if qty_num:
            for lookahead in range(1, 4):
                if i + lookahead < len(df):
                    if pd.isna(df.at[i, 'DESTINATION']): df.at[i, 'DESTINATION'] = df.at[i + lookahead, 'DESTINATION']
                    if pd.isna(df.at[i, 'ORIGIN']): df.at[i, 'ORIGIN'] = df.at[i + lookahead, 'ORIGIN']
                    if pd.isna(df.at[i, 'UNIT_TYPE']): df.at[i, 'UNIT_TYPE'] = df.at[i + lookahead, 'UNIT_TYPE']
    return df

def mark_order_block(df):
    df = df.copy(); df['BLOCK_ID'] = 0; current_block = 0
    last_header_text = ""
    header_pattern = r'(?im)^\s*.*(?:REQUEST|ONCALL|TAMBAHAN|ORDER|UNIT\s+ON\s+CALL|ON\s+CALL|TGL)\b.*$'
    for i in range(len(df)):
        qty_raw = str(df.at[i, 'UNIT_QTY'])
        is_header = False
        try:
            orig_text = str(df.at[i, 'Original_Text']) if 'Original_Text' in df.columns else ""
            q_num = extract_unit_qty(orig_text, qty_raw) or 0
            if q_num > 1: is_header = True
            elif q_num == 1 and pd.notna(df.at[i, 'UNIT_TYPE']): is_header = True
        except: pass
        orig_text = str(df.at[i, 'Original_Text']) if 'Original_Text' in df.columns else ""
        header_like = bool(re.search(header_pattern, orig_text)) if orig_text else False
        new_block = False
        if is_header:
            new_block = True
        elif header_like:
            text_key = orig_text.strip()
            if text_key and text_key != last_header_text:
                # Header request/oncall cukup untuk mulai block baru agar 1 unit tidak nempel block sebelumnya.
                new_block = True
        if new_block:
            current_block += 1
            if orig_text.strip():
                last_header_text = orig_text.strip()
        df.at[i, 'BLOCK_ID'] = current_block
    return df

def preprocess_context(df):
    if df is None or df.empty: return df
    required_cols = ['UNIT_TYPE', 'ORIGIN', 'DESTINATION', 'DATE', 'RO_DATE']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    df = repair_headers(df)
    df = mark_order_block(df)
    for col in required_cols:
        df[col] = df.groupby('BLOCK_ID')[col].ffill()
    return df

def enforce_block_quota(df):
    if df is None or df.empty: return df
    final_rows = []
    last_ro_date = ""

    def _clean_empty(val):
        if val is None:
            return ""
        try:
            if pd.isna(val):
                return ""
        except Exception:
            pass
        s = str(val).strip()
        if not s or s.lower() in ['nan', 'none', 'nat']:
            return ""
        return s

    def _compact(text):
        return re.sub(r'[^A-Z0-9]', '', str(text).upper())

    for block_id in df['BLOCK_ID'].unique():
        if block_id == 0: continue
        block_data = df[df['BLOCK_ID'] == block_id].copy()
        target_qty = 1
        explicit_qty_found = False
        extra_unit_count = 0
        seen_no_qty_headers = set()
        for _, r in block_data.iterrows():
            try:
                qty_num = extract_unit_qty(r.get('Original_Text', ''), r.get('UNIT_QTY', ''))
                if qty_num:
                    target_qty = max(target_qty, int(qty_num))
                    explicit_qty_found = True
            except: pass
        valid_candidates = []
        order_like_candidates = []
        header_row = None
        for _, row in block_data.iterrows():
            q_val = str(row.get('UNIT_QTY', ''))
            is_master_header = False
            try:
                q_num = extract_unit_qty(row.get('Original_Text', ''), q_val) or 0
                if q_num > 1: is_master_header = True
            except: pass
            if is_master_header:
                header_row = row
            # Baris revisi (Rev/Revisi/Update) hanya untuk update field, bukan order baru.
            orig_text_lower = str(row.get('Original_Text', '')).lower()
            if re.search(r'\b(?:rev|revisi|update)\b', orig_text_lower):
                continue

            # Jika tidak ada qty di header tapi ada order valid, hitung sebagai +1 unit.
            orig_text = str(row.get('Original_Text', '')).strip()
            if orig_text and orig_text not in seen_no_qty_headers:
                has_qty = bool(extract_unit_qty(row.get('Original_Text', ''), row.get('UNIT_QTY', '')))
                header_like = re.search(r'(?i)\brequest\b|\boncall\b', orig_text)
                order_like = re.search(r'(?i)\bLokasi\b|\bRute\b|\bWaktu\s*loading\b', orig_text)
                if not has_qty and header_like and order_like:
                    # Hitung jumlah order dari jumlah "Lokasi :" pada satu pesan tanpa qty.
                    lokasi_count = len(re.findall(r'(?im)^\s*Lokasi\s*:', orig_text))
                    extra_unit_count += max(1, lokasi_count)
                    seen_no_qty_headers.add(orig_text)

            row = sanitize_row_data(row)
            d_name = clean_driver_name(row.get('DRIVER', ''))
            if (not is_master_header) and (not str(row.get('PLATE', '')) or str(row.get('PLATE', '')).lower() == 'nan'):
                search_text = str(row.get('Original_Text', '')) + " " + str(row.get('DRIVER', ''))
                found_plate = extract_plate_aggressive(search_text)
                if found_plate: row['PLATE'] = found_plate
            has_plate = pd.notna(row.get('PLATE')) and len(str(row.get('PLATE'))) > 3
            added_as_candidate = False
            has_phone = pd.notna(row.get('PHONE')) and len(str(row.get('PHONE')).strip()) > 5
            if d_name or has_plate or has_phone:
                row['DRIVER'] = d_name
                valid_candidates.append(row)
                added_as_candidate = True

            if not explicit_qty_found and not added_as_candidate:
                orig_text = str(row.get('Original_Text', '')).strip()
                order_like = False
                if normalize_origin(row.get('ORIGIN', '')) or normalize_route(row.get('DESTINATION', '')):
                    order_like = True
                elif re.search(r'(?i)\b(Lokasi|Rute|Waktu\s*loading)\b', orig_text):
                    order_like = True
                if order_like:
                    order_like_candidates.append(row)
        if header_row is None and len(block_data) > 0: header_row = block_data.iloc[0]
        header_row = normalize_header_context_fields(header_row)

        if not explicit_qty_found and order_like_candidates:
            valid_candidates.extend(order_like_candidates)
            target_qty = max(1, len(valid_candidates))
        elif explicit_qty_found and extra_unit_count:
            # Jika qty eksplisit sudah ada, jangan menambah quota dari header tanpa qty.
            # Ini mencegah duplikasi target_qty pada block yang sudah jelas jumlah unitnya.
            pass

        block_text = ""
        try:
            text_series = block_data['Original_Text'] if 'Original_Text' in block_data.columns else []
            if len(text_series) > 0:
                block_text = max([str(x) for x in text_series if str(x).strip()], key=len, default="")
        except:
            block_text = ""
        block_route_from_text = normalize_route(extract_route_from_text(block_text)) if block_text else ""
        block_driver_pair = ""
        if block_text:
            bd1, bd2 = extract_driver_pair_from_text(block_text)
            if bd1 and bd2:
                block_driver_pair = f"{bd1} & {bd2}" if bd1.lower() != bd2.lower() else bd1
        block_plate = extract_plate_aggressive(block_text) if block_text else ""
        block_phone_pair = ""
        if block_text and block_driver_pair:
            bp1, bp2 = extract_phone_pair_from_text(block_text)
            if bp1 and bp2:
                block_phone_pair = bp1 if bp1 == bp2 else f"{bp1} & {bp2}"

        origin_pool = []
        destination_pool = []
        for src_row in [header_row] + valid_candidates:
            o = normalize_origin(src_row.get('ORIGIN', ''))
            d = normalize_route(src_row.get('DESTINATION', ''))
            if o:
                origin_pool.append(o)
            if d:
                destination_pool.append(d)

        if origin_pool:
            block_origin = max(origin_pool, key=lambda x: (len(x.split()), len(x)))
            header_row['ORIGIN'] = block_origin
        else:
            block_origin = normalize_origin(header_row.get('ORIGIN', ''))

        if block_route_from_text:
            block_destination = block_route_from_text
            header_row['DESTINATION'] = block_destination
        elif destination_pool:
            with_separator = [d for d in destination_pool if ',' in d]
            block_destination = with_separator[0] if with_separator else destination_pool[0]
            header_row['DESTINATION'] = block_destination
        else:
            block_destination = normalize_route(header_row.get('DESTINATION', ''))

        block_ro_date = _clean_empty(header_row.get('RO_DATE', ''))
        if not block_ro_date:
            for src_row in [header_row] + valid_candidates:
                candidate_ro = _clean_empty(src_row.get('RO_DATE', ''))
                if candidate_ro:
                    block_ro_date = candidate_ro
                    break
        if not block_ro_date and block_text:
            ro_from_block = extract_ro_date_from_text(block_text)
            if ro_from_block:
                block_ro_date = ro_from_block
        if not block_ro_date and last_ro_date:
            block_ro_date = last_ro_date
        if block_ro_date:
            header_row['RO_DATE'] = block_ro_date
            last_ro_date = block_ro_date

        block_muat_date = ""
        for src_row in valid_candidates:
            candidate_date = str(src_row.get('DATE', '')).strip()
            if candidate_date:
                block_muat_date = candidate_date
                break
        # Ambil urutan Waktu loading dalam block untuk pemetaan berurutan
        loading_queue = {}
        block_has_segera = False
        block_dates = []
        loading_candidates_list = []
        loading_details_list = []
        time_date_map = {}
        if 'Original_Text' in block_data.columns:
            seen_texts = set()
            for txt in block_data['Original_Text']:
                s = str(txt).strip()
                if not s or s in seen_texts:
                    continue
                seen_texts.add(s)
                if not block_has_segera and re.search(r'(?i)\bsegera\b', s):
                    block_has_segera = True
                loading_candidates_list.extend(extract_loading_candidates(s))
                loading_details_list.extend(extract_loading_details(s))
        elif block_text:
            loading_candidates_list = extract_loading_candidates(block_text)
            loading_details_list = extract_loading_details(block_text)
        for lc in loading_candidates_list:
            if lc.get('segera'):
                block_has_segera = True
            if lc.get('date'):
                block_dates.append(lc.get('date'))
            t_key = str(lc.get('time', '')).strip().upper()
            if not t_key:
                continue
            loading_queue.setdefault(t_key, []).append(lc)
            if lc.get('date') and t_key not in time_date_map:
                time_date_map[t_key] = lc.get('date')

        # Urutan loading dipakai untuk mengisi slot partial (clean_slot) agar
        # tanggal per unit mengikuti urutan Waktu loading pada pesan asli.
        loading_sequence = []
        for idx_lc, lc in enumerate(loading_candidates_list):
            item = {
                "time": str(lc.get("time", "")).strip(),
                "date": str(lc.get("date", "")).strip(),
                "segera": bool(lc.get("segera")),
                "driver": "",
                "plate": "",
                "phone": "",
            }
            if idx_lc < len(loading_details_list):
                det = loading_details_list[idx_lc]
                item["driver"] = clean_driver_name(det.get("driver", ""))
                item["plate"] = clean_plate_value(det.get("plate", ""))
                item["phone"] = normalize_phone_number(det.get("phone", ""))
            loading_sequence.append(item)
        loading_slots = [dict(x) for x in loading_sequence]

        def _identity_key(driver_val="", plate_val="", phone_val=""):
            d = clean_driver_name(driver_val).upper()
            p = clean_plate_value(plate_val).upper()
            ph = normalize_phone_number(phone_val)
            return f"{d}|{p}|{ph}"

        def _extract_identity_profiles_from_text(text):
            """
            Ambil daftar identitas berurutan dari blok teks.
            Fokus pada pola:
            Driver : ...
            Nopol  : ...
            No Hp  : ...
            """
            if not text:
                return []
            text = normalize_field_labels_in_text(text)

            profiles = []
            current = {"driver": "", "plate": "", "phone": ""}

            def _flush_current():
                nonlocal current
                d = clean_driver_name(current.get("driver", ""))
                p = clean_plate_value(current.get("plate", ""))
                ph = normalize_phone_number(current.get("phone", ""))
                if d or p or ph:
                    profiles.append({"driver": d, "plate": p, "phone": ph})
                current = {"driver": "", "plate": "", "phone": ""}

            lines = re.split(r'[\r\n]+', str(text))
            for raw_line in lines:
                line = str(raw_line).strip()
                if not line:
                    continue

                # Waktu loading baru = batas segmen.
                if re.search(r'(?i)^Waktu\s*loading\s*:', line):
                    _flush_current()
                    continue

                drv_match = re.search(
                    r'(?i)^\s*(?:d+driver|driver|pengemudi)(?:\s*\d+)?\s*[:.]?\s*(.*)$',
                    line
                )
                if drv_match:
                    if current.get("driver") or current.get("plate") or current.get("phone"):
                        _flush_current()
                    current["driver"] = clean_driver_name(drv_match.group(1))
                    continue

                plate_match = re.search(
                    r'(?i)^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*[:.]?\s*(.*)$',
                    line,
                )
                if plate_match:
                    current["plate"] = clean_plate_value(plate_match.group(1))
                    continue

                phone_match = re.search(
                    r'(?i)^\s*(?:no\.?\s*hp|hp|no\.?\s*telp|no\.?\s*tlp|kontak)\s*[:.]?\s*(.*)$',
                    line,
                )
                if phone_match:
                    current["phone"] = normalize_phone_number(phone_match.group(1))
                    continue

            _flush_current()

            unique_profiles = []
            seen = set()
            for p in profiles:
                k = _identity_key(p.get("driver", ""), p.get("plate", ""), p.get("phone", ""))
                if k == "||" or k in seen:
                    continue
                seen.add(k)
                unique_profiles.append(p)
            return unique_profiles

        # Kasus khusus: 1 Waktu loading tetapi ada lebih dari 1 blok Driver/Nopol/HP
        # dalam pesan yang sama. Tambahkan slot identitas ekstra tanpa mengubah kuota.
        driver_line_count = 0
        if block_text:
            driver_line_count = len(
                re.findall(
                    r'(?im)^\s*(?:d+driver|driver|pengemudi)(?:\s*\d+)?\s*[:.]?',
                    normalize_field_labels_in_text(block_text),
                )
            )
        if (
            block_text
            and target_qty > len(loading_slots)
            and len(loading_candidates_list) <= 1
            and driver_line_count >= 2
        ):
            profile_list = _extract_identity_profiles_from_text(block_text)
            if profile_list:
                existing_identity = set()
                for slot in loading_slots:
                    s_key = _identity_key(slot.get("driver", ""), slot.get("plate", ""), slot.get("phone", ""))
                    if s_key != "||":
                        existing_identity.add(s_key)

                base_slot = loading_slots[0] if loading_slots else {}
                base_time = str(base_slot.get("time", "")).strip()
                base_date = str(base_slot.get("date", "")).strip()
                base_segera = bool(base_slot.get("segera", False))

                for p in profile_list:
                    p_key = _identity_key(p.get("driver", ""), p.get("plate", ""), p.get("phone", ""))
                    if p_key == "||" or p_key in existing_identity:
                        continue
                    if len(loading_slots) >= target_qty:
                        break
                    extra_slot = {
                        "time": base_time,
                        "date": base_date,
                        "segera": base_segera,
                        "driver": p.get("driver", ""),
                        "plate": p.get("plate", ""),
                        "phone": p.get("phone", ""),
                    }
                    loading_slots.append(dict(extra_slot))
                    loading_sequence.append(dict(extra_slot))
                    existing_identity.add(p_key)

        # Jika ada minimal satu slot yang punya identitas eksplisit, maka slot lain yang
        # identitasnya kosong dianggap memang kosong (jangan diwarisi dari kandidat lain).
        slot_identity_available = any(
            clean_driver_name(x.get("driver", ""))
            or clean_plate_value(x.get("plate", ""))
            or normalize_phone_number(x.get("phone", ""))
            for x in loading_slots
        )
        strict_slot_identity_mode = slot_identity_available and len(loading_slots) >= target_qty

        if strict_slot_identity_mode and valid_candidates:
            slot_time_has_identity = {}
            slot_identity_limit = {}
            for slot in loading_slots:
                t_key = str(slot.get("time", "")).strip().upper()
                has_identity = bool(
                    clean_driver_name(slot.get("driver", ""))
                    or clean_plate_value(slot.get("plate", ""))
                    or normalize_phone_number(slot.get("phone", ""))
                )
                if t_key and t_key not in slot_time_has_identity:
                    slot_time_has_identity[t_key] = has_identity
                if has_identity:
                    s_key = _identity_key(slot.get("driver", ""), slot.get("plate", ""), slot.get("phone", ""))
                    slot_identity_limit[s_key] = slot_identity_limit.get(s_key, 0) + 1

            seen_identity = {}
            for idx_cand, cand in enumerate(valid_candidates):
                cand_key = _identity_key(cand.get("DRIVER", ""), cand.get("PLATE", ""), cand.get("PHONE", ""))
                if cand_key == "||":
                    continue

                cand_time_key = str(cand.get("TIME", "")).strip().upper()
                should_clear = False

                if cand_time_key and cand_time_key in slot_time_has_identity and not slot_time_has_identity[cand_time_key]:
                    should_clear = True

                if not should_clear:
                    allowed = slot_identity_limit.get(cand_key, 0)
                    used = seen_identity.get(cand_key, 0)
                    if allowed == 0 or used >= allowed:
                        should_clear = True
                    else:
                        seen_identity[cand_key] = used + 1

                if should_clear:
                    cand['DRIVER'] = ""
                    cand['PLATE'] = ""
                    cand['PHONE'] = ""
                    valid_candidates[idx_cand] = cand

        def _consume_loading_sequence(preferred_time_key=""):
            if not loading_sequence:
                return None
            pref = str(preferred_time_key).strip().upper()
            if pref:
                for idx, item in enumerate(loading_sequence):
                    item_key = str(item.get("time", "")).strip().upper()
                    if item_key and item_key == pref:
                        return loading_sequence.pop(idx)
            return loading_sequence.pop(0)

        def _valid_time_token(time_val):
            t = str(time_val).strip().upper()
            if not t:
                return ""
            if t == "SEGERA":
                return "SEGERA"
            if re.match(r'^\d{1,2}:\d{2}$', t):
                return t
            return ""

        def _apply_identity_from_seq(row_obj, seq_item, overwrite=False):
            if not seq_item:
                return
            seq_driver = clean_driver_name(seq_item.get("driver", ""))
            seq_plate = clean_plate_value(seq_item.get("plate", ""))
            seq_phone = normalize_phone_number(seq_item.get("phone", ""))

            if seq_driver and (overwrite or not str(row_obj.get('DRIVER', '')).strip()):
                row_obj['DRIVER'] = seq_driver
            if seq_plate and (overwrite or not str(row_obj.get('PLATE', '')).strip()):
                row_obj['PLATE'] = seq_plate
            if seq_phone and (overwrite or not str(row_obj.get('PHONE', '')).strip()):
                row_obj['PHONE'] = seq_phone

        def _apply_datetime_from_seq(row_obj, seq_item, force=False):
            if not seq_item:
                return
            seq_time = _valid_time_token(seq_item.get("time", ""))
            seq_date = str(seq_item.get("date", "")).strip()
            seq_is_segera = bool(seq_item.get("segera"))
            cur_time = str(row_obj.get("TIME", "")).strip()
            cur_date = str(row_obj.get("DATE", "")).strip()
            if seq_time and (force or not cur_time):
                row_obj["TIME"] = seq_time
            if seq_date:
                if force:
                    row_obj["DATE"] = seq_date
                elif (not cur_date) or (block_ro_date and cur_date == block_ro_date and seq_date != block_ro_date):
                    row_obj["DATE"] = seq_date
            elif force and seq_is_segera and block_ro_date:
                # Slot SEGERA tanpa tanggal eksplisit harus tetap ikut Tgl RO block.
                row_obj["DATE"] = block_ro_date
        if not block_muat_date and block_dates:
            block_muat_date = block_dates[0]
        if not block_muat_date and block_has_segera and block_ro_date:
            block_muat_date = block_ro_date
        # Jika tidak ada Waktu loading sama sekali di block yang punya qty eksplisit,
        # anggap SEGERA -> Tgl Muat mengikuti Tgl RO.
        if not block_muat_date and not loading_candidates_list and explicit_qty_found and block_ro_date:
            block_muat_date = block_ro_date
            block_has_segera = True

        for i in range(target_qty):
            if i < len(valid_candidates):
                candidate = valid_candidates[i]
                matched_loading_sequence = False
                identity_locked_blank = False

                cand_origin = normalize_origin(candidate.get('ORIGIN', ''))
                if not cand_origin:
                    cand_origin = block_origin
                elif block_origin and cand_origin != block_origin:
                    cand_tokens = set(cand_origin.split())
                    block_tokens = set(block_origin.split())
                    if cand_tokens and cand_tokens.issubset(block_tokens):
                        cand_origin = block_origin
                candidate['ORIGIN'] = cand_origin

                cand_destination = normalize_route(candidate.get('DESTINATION', ''))
                if not cand_destination:
                    cand_destination = block_destination
                elif block_destination and cand_destination == block_origin:
                    cand_destination = block_destination
                elif block_destination and cand_destination != block_destination:
                    if ',' in block_destination and _compact(cand_destination) == _compact(block_destination):
                        cand_destination = block_destination
                candidate['DESTINATION'] = cand_destination

                # RO_DATE harus konsisten per block.
                if block_ro_date:
                    candidate['RO_DATE'] = block_ro_date

                # Selaraskan Tgl Muat berdasarkan urutan Waktu loading jika ada.
                cand_time_key = str(candidate.get('TIME', '')).strip().upper()
                cand_date_existing = str(candidate.get('DATE', '')).strip()
                # Sinkronkan konsumsi urutan loading agar slot partial berikutnya
                # tidak mengambil slot waktu yang sudah dipakai kandidat ini.
                if cand_time_key:
                    seq_used = _consume_loading_sequence(cand_time_key)
                    if seq_used:
                        seq_used_has_identity = bool(
                            clean_driver_name(seq_used.get("driver", ""))
                            or clean_plate_value(seq_used.get("plate", ""))
                            or normalize_phone_number(seq_used.get("phone", ""))
                        )
                        if slot_identity_available and not seq_used_has_identity:
                            candidate['DRIVER'] = ""
                            candidate['PLATE'] = ""
                            candidate['PHONE'] = ""
                            identity_locked_blank = True
                        # Jika slot waktu sudah cocok, detail segmen adalah sumber utama.
                        _apply_identity_from_seq(candidate, seq_used, overwrite=True)
                        matched_loading_sequence = True
                elif i == 0 and loading_sequence:
                    # Jika kandidat utama tidak punya TIME (umum pada hasil model),
                    # tetapi blok dimulai dari "SEGERA", anggap slot pertama sudah
                    # terwakili oleh kandidat utama agar mapping slot partial tetap urut.
                    first_seq = loading_sequence[0] if loading_sequence else None
                    cand_has_identity = bool(
                        str(candidate.get('DRIVER', '')).strip()
                        or str(candidate.get('PLATE', '')).strip()
                        or str(candidate.get('PHONE', '')).strip()
                    )
                    if cand_has_identity and first_seq and bool(first_seq.get("segera")):
                        seq_used = _consume_loading_sequence()
                        seq_used_has_identity = bool(
                            clean_driver_name(seq_used.get("driver", "")) if seq_used else ""
                            or clean_plate_value(seq_used.get("plate", "")) if seq_used else ""
                            or normalize_phone_number(seq_used.get("phone", "")) if seq_used else ""
                        )
                        if slot_identity_available and not seq_used_has_identity:
                            candidate['DRIVER'] = ""
                            candidate['PLATE'] = ""
                            candidate['PHONE'] = ""
                            identity_locked_blank = True
                        _apply_identity_from_seq(candidate, seq_used, overwrite=True)
                        matched_loading_sequence = True
                if cand_time_key and cand_time_key in loading_queue and loading_queue[cand_time_key]:
                    lc = loading_queue[cand_time_key].pop(0)
                    if not cand_date_existing:
                        if lc.get("segera"):
                            candidate['DATE'] = block_ro_date if block_ro_date else candidate.get('RO_DATE', '')
                        elif lc.get("date"):
                            candidate['DATE'] = lc.get("date")
                        else:
                            candidate['DATE'] = block_ro_date if block_ro_date else candidate.get('RO_DATE', '')
                    if not str(candidate.get('TIME', '')).strip() and lc.get("time"):
                        candidate['TIME'] = lc.get("time")
                elif cand_time_key:
                    if cand_time_key in time_date_map:
                        mapped_date = time_date_map[cand_time_key]
                        if (not cand_date_existing) or (block_ro_date and cand_date_existing == block_ro_date and mapped_date != block_ro_date):
                            candidate['DATE'] = mapped_date

                # Jika Tgl Muat kosong:
                # - Jika ada JAM, Tgl Muat mengikuti Tgl RO.
                # - Jika tidak ada JAM, baru boleh ikut Tgl Muat block (jika ada).
                if not str(candidate.get('DATE', '')).strip():
                    cand_time = str(candidate.get('TIME', '')).strip()
                    if cand_time:
                        if block_ro_date:
                            candidate['DATE'] = block_ro_date
                        elif block_muat_date:
                            candidate['DATE'] = block_muat_date
                    elif block_has_segera and block_ro_date:
                        candidate['DATE'] = block_ro_date
                    elif block_muat_date:
                        candidate['DATE'] = block_muat_date
                else:
                    # Jika DATE terisi sama dengan Tgl RO tetapi blok punya Tgl Muat berbeda
                    # dan baris ini tidak punya JAM, utamakan Tgl Muat blok.
                    cand_time = str(candidate.get('TIME', '')).strip()
                    cand_date_existing = str(candidate.get('DATE', '')).strip()
                    if (not cand_time) and block_muat_date and block_ro_date:
                        if cand_date_existing == block_ro_date and block_muat_date != block_ro_date:
                            candidate['DATE'] = block_muat_date

                for col in ['UNIT_TYPE', 'DATE', 'RO_DATE']:
                    val = candidate.get(col)
                    if pd.isna(val) or str(val).strip() == "":
                        header_val = _clean_empty(header_row.get(col))
                        if col == 'DATE':
                            if header_val and (re.search(r'\d', str(header_val))): candidate[col] = header_val
                        else:
                            candidate[col] = header_val
                if (not identity_locked_blank) and (not str(candidate.get('DRIVER', '')).strip()) and block_driver_pair:
                    candidate['DRIVER'] = block_driver_pair
                if (not identity_locked_blank) and (not str(candidate.get('PLATE', '')).strip()) and block_plate:
                    candidate['PLATE'] = block_plate
                if (not identity_locked_blank) and (not str(candidate.get('PHONE', '')).strip()) and block_phone_pair:
                    candidate['PHONE'] = block_phone_pair
                # Guardrail: urutan slot dari teks asli jadi acuan utama per indeks unit.
                if i < len(loading_slots):
                    seq_slot = loading_slots[i]
                    seq_has_identity = bool(
                        clean_driver_name(seq_slot.get("driver", ""))
                        or clean_plate_value(seq_slot.get("plate", ""))
                        or normalize_phone_number(seq_slot.get("phone", ""))
                    )
                    if slot_identity_available and (not seq_has_identity) and (not matched_loading_sequence):
                        candidate['DRIVER'] = ""
                        candidate['PLATE'] = ""
                        candidate['PHONE'] = ""
                    _apply_identity_from_seq(candidate, seq_slot, overwrite=True)
                    # Guardrail utama: tanggal/jam per unit mengikuti urutan slot teks asli.
                    _apply_datetime_from_seq(candidate, seq_slot, force=True)
                final_rows.append(candidate)
            else:
                clean_slot = header_row.copy()
                clean_slot['DRIVER'] = ""; clean_slot['PLATE'] = ""; clean_slot['PHONE'] = ""; clean_slot['TIME'] = ""; clean_slot['UNIT_QTY'] = 1
                header_date = _clean_empty(header_row.get('DATE'))
                if header_date and re.search(r'\d', str(header_date)): clean_slot['DATE'] = header_date
                else: clean_slot['DATE'] = ""
                if block_ro_date:
                    clean_slot['RO_DATE'] = block_ro_date
                seq_slot = _consume_loading_sequence()
                if seq_slot:
                    seq_time = _valid_time_token(seq_slot.get("time", ""))
                    seq_date = str(seq_slot.get("date", "")).strip()
                    if seq_time:
                        clean_slot['TIME'] = seq_time
                    _apply_identity_from_seq(clean_slot, seq_slot, overwrite=True)
                    if seq_date:
                        clean_slot['DATE'] = seq_date
                    elif seq_slot.get("segera") and block_ro_date:
                        clean_slot['DATE'] = block_ro_date
                    elif seq_time and block_ro_date:
                        clean_slot['DATE'] = block_ro_date
                    elif block_muat_date:
                        clean_slot['DATE'] = block_muat_date
                elif block_muat_date:
                    clean_slot['DATE'] = block_muat_date
                elif block_has_segera and block_ro_date:
                    clean_slot['DATE'] = block_ro_date
                if i < len(loading_slots):
                    seq_slot = loading_slots[i]
                    seq_has_identity = bool(
                        clean_driver_name(seq_slot.get("driver", ""))
                        or clean_plate_value(seq_slot.get("plate", ""))
                        or normalize_phone_number(seq_slot.get("phone", ""))
                    )
                    if slot_identity_available and not seq_has_identity:
                        clean_slot['DRIVER'] = ""
                        clean_slot['PLATE'] = ""
                        clean_slot['PHONE'] = ""
                    _apply_identity_from_seq(clean_slot, seq_slot, overwrite=True)
                    _apply_datetime_from_seq(clean_slot, seq_slot, force=True)
                final_rows.append(clean_slot)
    return pd.DataFrame(final_rows).reset_index(drop=True)

# --- [FALLBACK] REVISI BERBASIS RULE ENGINE LAMA ---
def _apply_revisions_from_chat_rule_engine(chat_text, df_final):
    """
    Fallback engine untuk menjaga kompatibilitas kualitas ketika
    confidence ML rendah / ambigu.
    """
    if df_final is None or df_final.empty or not chat_text:
        return df_final

    df = df_final.copy()
    wa_pattern = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
    messages = [m for m in re.split(wa_pattern, str(chat_text)) if str(m).strip()]

    def normalize_time(time_str):
        if not time_str:
            return None
        s = str(time_str).strip().replace('.', ':')
        if not s:
            return None
        if "SEGERA" in s.upper():
            return "SEGERA"
        m = re.search(r'(\d{1,2})(?::(\d{2}))?', s)
        if m:
            hour = int(m.group(1))
            minute = m.group(2) if m.group(2) else "00"
            return f"{hour:02d}:{minute}"
        return None

    def has_revision_keyword(text):
        return bool(re.search(r'(?i)\b(?:rev|revisi|update)\b', str(text)))

    def normalize_token(text):
        if text is None:
            return ""
        return re.sub(r'\s+', ' ', str(text).upper()).strip()

    def extract_revision_payload(msg_text):
        msg_text = normalize_field_labels_in_text(msg_text)
        payload = {
            'target_time': None,
            'target_origin': "",
            'target_route': "",
            'target_unit': "",
            'updates': {}
        }

        time_match = re.search(r'(?i)(?:jam|pukul|waktu(?:\s+loading)?)\s*:?\s*(\d{1,2}(?:[:.]\d{2})?)', msg_text)
        if time_match:
            payload['target_time'] = normalize_time(time_match.group(1))

        lokasi_match = re.search(r'(?im)^\s*Lokasi\s*:\s*([^\n\r]+)', msg_text)
        if lokasi_match:
            payload['target_origin'] = normalize_token(lokasi_match.group(1))

        route_match = re.search(r'(?im)^\s*Rute(?:\s*/\s*|\s+)tujuan\s*:\s*([^\n\r]+)', msg_text)
        if route_match:
            payload['target_route'] = normalize_route(route_match.group(1))

        unit_match = re.search(r'(?im)^\s*(?:jenis\s+unit|type\s+truck)\s*:\s*([^\n\r]+)', msg_text)
        if unit_match:
            payload['target_unit'] = normalize_unit_type(unit_match.group(1))
        else:
            unit_inline = re.search(r'(?i)\bunit\s+([a-zA-Z][a-zA-Z0-9\s]{1,20})', msg_text)
            if unit_inline:
                unit_candidate = unit_inline.group(1).strip()
                if not re.match(r'(?i)^(?:jam|pukul|waktu)\b', unit_candidate):
                    payload['target_unit'] = normalize_unit_type(unit_candidate)

        for line in str(msg_text).split('\n'):
            line = line.strip()
            if not line:
                continue

            plate_match = re.search(r'(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:?\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})', line, re.IGNORECASE)
            if plate_match:
                payload['updates']['PLATE'] = plate_match.group(1).strip().upper()

            driver_match = re.search(r'(?:driver|pengemudi)\s*:?\s*([a-zA-Z\s]+)', line, re.IGNORECASE)
            if driver_match and not has_revision_keyword(driver_match.group(1)):
                d_name = clean_driver_name(driver_match.group(1).strip())
                if d_name:
                    payload['updates']['DRIVER'] = d_name

            phone_match = re.search(r'(?:no\.?\s*hp|hp|no\.?\s*telp|kontak)\s*:?\s*([0-9+\-\s]+)', line, re.IGNORECASE)
            if phone_match:
                payload['updates']['PHONE'] = normalize_phone_number(phone_match.group(1).strip())

        return payload

    revision_mask = pd.Series(False, index=df.index)
    if 'Original_Text' in df.columns:
        revision_mask = df['Original_Text'].apply(has_revision_keyword)

    def row_time(idx):
        return normalize_time(df.at[idx, 'TIME']) if 'TIME' in df.columns else None

    def row_origin(idx):
        return normalize_token(df.at[idx, 'ORIGIN']) if 'ORIGIN' in df.columns else ""

    def row_route(idx):
        if 'DESTINATION' not in df.columns:
            return ""
        return normalize_route(df.at[idx, 'DESTINATION'])

    def row_unit(idx):
        if 'UNIT_TYPE' not in df.columns:
            return ""
        return normalize_unit_type(df.at[idx, 'UNIT_TYPE'])

    def pick_best(candidates, payload):
        if not candidates:
            return None
        scored = []
        for idx in candidates:
            score = 0
            if payload['target_origin'] and row_origin(idx) == payload['target_origin']:
                score += 1
            if payload['target_route'] and row_route(idx) == payload['target_route']:
                score += 1
            if payload['target_unit'] and row_unit(idx) == payload['target_unit']:
                score += 1
            scored.append((score, idx))
        max_score = max(s for s, _ in scored)
        best = [idx for s, idx in scored if s == max_score]
        return max(best)

    def find_best_match(payload):
        candidate_indices = [idx for idx in df.index if not bool(revision_mask.loc[idx])]
        if not candidate_indices:
            return None

        if payload['target_time']:
            by_time = [idx for idx in candidate_indices if row_time(idx) == payload['target_time']]
            if by_time:
                return pick_best(by_time, payload)

        if payload['target_origin']:
            by_origin = [idx for idx in candidate_indices if row_origin(idx) == payload['target_origin']]
            if by_origin:
                return pick_best(by_origin, payload)

        if payload['target_route']:
            by_route = [idx for idx in candidate_indices if row_route(idx) == payload['target_route']]
            if by_route:
                return pick_best(by_route, payload)

        return max(candidate_indices)

    for msg in messages:
        if not has_revision_keyword(msg):
            continue
        payload = extract_revision_payload(msg)
        if not payload['updates']:
            continue
        target_idx = find_best_match(payload)
        if target_idx is None:
            continue

        for field, value in payload['updates'].items():
            if field in df.columns:
                df.at[target_idx, field] = value

    return df


def _get_revision_matcher():
    global _REVISION_MATCHER_INSTANCE, _REVISION_MATCHER_LOAD_FAILED
    if not APP_REVISION_ML_ENABLED:
        return None
    if _REVISION_MATCHER_INSTANCE is not None:
        return _REVISION_MATCHER_INSTANCE
    if _REVISION_MATCHER_LOAD_FAILED:
        return None
    if not APP_REVISION_MATCHER_MODEL_PATH:
        _REVISION_MATCHER_LOAD_FAILED = True
        print("[WARN] Model revision matcher belum tersedia.")
        return None
    try:
        _REVISION_MATCHER_INSTANCE = RevisionMatcherInference(APP_REVISION_MATCHER_MODEL_PATH)
    except Exception as e:
        _REVISION_MATCHER_LOAD_FAILED = True
        print(f"[WARN] Gagal memuat revision matcher: {e}")
        return None
    return _REVISION_MATCHER_INSTANCE


def _get_event_classifier():
    global _EVENT_CLASSIFIER_INSTANCE, _EVENT_CLASSIFIER_LOAD_FAILED
    if _EVENT_CLASSIFIER_INSTANCE is not None:
        return _EVENT_CLASSIFIER_INSTANCE
    if _EVENT_CLASSIFIER_LOAD_FAILED:
        return None
    if not APP_EVENT_MODEL_PATH:
        _EVENT_CLASSIFIER_LOAD_FAILED = True
        return None
    try:
        _EVENT_CLASSIFIER_INSTANCE = EventClassifierInference(APP_EVENT_MODEL_PATH)
    except Exception as e:
        _EVENT_CLASSIFIER_LOAD_FAILED = True
        print(f"[WARN] Gagal memuat event classifier (optional): {e}")
        return None
    return _EVENT_CLASSIFIER_INSTANCE


def _revml_normalize_time(value):
    if value is None:
        return ""
    s = str(value).strip().replace(".", ":")
    if not s:
        return ""
    if "SEGERA" in s.upper():
        return "SEGERA"
    m = re.search(r"(\d{1,2})(?::(\d{2}))?", s)
    if not m:
        return ""
    hour = int(m.group(1))
    minute = m.group(2) if m.group(2) else "00"
    return f"{hour:02d}:{minute}"


def _normalize_message_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().upper()


def _split_wa_messages(chat_text):
    wa_pattern = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
    messages = [m for m in re.split(wa_pattern, str(chat_text)) if str(m).strip()]
    return messages if messages else [str(chat_text)]


def _build_match_candidate_text(row):
    def _v(key):
        return str(row.get(key, "") or "").strip()

    ro_date = _v("RO_DATE") or _v("DATE")
    load_date = _v("DATE")
    structured = "\n".join(
        [
            f"RO_DATE: {ro_date or '-'}",
            f"LOAD_DATE: {load_date or '-'}",
            f"TIME: {_revml_normalize_time(_v('TIME')) or '-'}",
            f"ORIGIN: {normalize_origin(_v('ORIGIN')) or '-'}",
            f"DESTINATION: {normalize_route(_v('DESTINATION')) or '-'}",
            f"UNIT_TYPE: {normalize_unit_type(_v('UNIT_TYPE')) or '-'}",
            f"DRIVER: {clean_driver_name(_v('DRIVER')) or '-'}",
            f"PLATE: {clean_plate_value(_v('PLATE')) or '-'}",
            f"PHONE: {normalize_phone_number(_v('PHONE')) or '-'}",
        ]
    )
    original = _v("Original_Text")
    return f"{original}\n{structured}".strip() if original else structured


def _build_match_query_text(payload):
    updates = payload.get("updates", {}) or {}
    ro_date = payload.get("target_ro_date", "") or updates.get("RO_DATE", "")
    load_date = payload.get("target_load_date", "") or updates.get("DATE", "")
    time_val = payload.get("target_time", "") or updates.get("TIME", "")
    origin = payload.get("target_origin", "") or updates.get("ORIGIN", "")
    destination = payload.get("target_route", "") or updates.get("DESTINATION", "")
    unit_type = payload.get("target_unit", "") or updates.get("UNIT_TYPE", "")
    driver = updates.get("DRIVER", "")
    plate = updates.get("PLATE", "")
    phone = updates.get("PHONE", "")
    return "\n".join(
        [
            "REQUEST ULANG ORDER ONCALL",
            f"RO_DATE: {ro_date or '-'}",
            f"LOAD_DATE: {load_date or '-'}",
            f"TIME: {_revml_normalize_time(time_val) or '-'}",
            f"ORIGIN: {normalize_origin(origin) or '-'}",
            f"DESTINATION: {normalize_route(destination) or '-'}",
            f"UNIT_TYPE: {normalize_unit_type(unit_type) or '-'}",
            f"DRIVER: {clean_driver_name(driver) or '-'}",
            f"PLATE: {clean_plate_value(plate) or '-'}",
            f"PHONE: {normalize_phone_number(phone) or '-'}",
        ]
    )


def _row_needs_refill(row):
    driver_blank = not clean_driver_name(row.get("DRIVER", ""))
    plate_blank = not clean_plate_value(row.get("PLATE", ""))
    phone_blank = not normalize_phone_number(row.get("PHONE", ""))
    return driver_blank or plate_blank or phone_blank


def _predict_update_event(message_text, event_classifier):
    if event_classifier is None:
        return "", 0.0
    try:
        pred = event_classifier.predict(message_text)
        return str(pred.get("label", "")).upper(), float(pred.get("score", 0.0))
    except Exception:
        return "", 0.0


def _is_update_event_message(message_text, event_classifier):
    event_label, event_score = _predict_update_event(message_text, event_classifier)
    has_update_keyword = bool(
        re.search(
            r"(?i)\b(?:rev|revisi|update|ubah|ganti|ulang|tambahan|perbaikan|refill)\b",
            str(message_text or ""),
        )
    )
    is_update_event = (event_label == "UPDATE" and event_score >= APP_EVENT_THRESHOLD) or has_update_keyword
    return is_update_event, event_label, event_score, has_update_keyword


def _revision_payload_context_compatible(payload, row_data):
    target_origin = payload.get("target_origin", "")
    target_route = payload.get("target_route", "")
    target_unit = payload.get("target_unit", "")
    target_time = payload.get("target_time", "")

    row_origin = normalize_origin(row_data.get("ORIGIN", ""))
    row_route = normalize_route(row_data.get("DESTINATION", ""))
    row_unit = normalize_unit_type(row_data.get("UNIT_TYPE", ""))
    row_time = _revml_normalize_time(row_data.get("TIME", ""))

    if target_origin and row_origin and target_origin != row_origin:
        return False
    if target_route and row_route and target_route != row_route:
        return False
    if target_unit and row_unit and target_unit != row_unit:
        return False
    if target_time and row_time and target_time != row_time:
        return False
    return True


def _build_match_candidates_for_payload(df, payload, mode, revision_mask, source_index_set, reserved_targets):
    strict_candidates = []
    broad_candidates = []
    for idx in df.index:
        if bool(revision_mask.loc[idx]):
            continue
        if idx in source_index_set or idx in reserved_targets:
            continue
        row = df.loc[idx]
        if mode == "REFILL" and not _row_needs_refill(row):
            continue

        candidate_item = {
            "candidate_index": int(idx),
            "candidate_text": _build_match_candidate_text(row),
        }
        broad_candidates.append(candidate_item)
        if _revision_payload_context_compatible(payload, row):
            strict_candidates.append(candidate_item)

    return strict_candidates, broad_candidates


def _select_target_with_matcher(matcher, query_text, strict_candidates, broad_candidates):
    result = {
        "attempted": False,
        "resolved": False,
        "target_idx": None,
        "ranked": [],
        "best_probability": 0.0,
        "second_probability": 0.0,
        "probability_gap": 0.0,
        "candidate_count": 0,
        "has_strict_context": bool(strict_candidates),
    }
    if matcher is None:
        return result

    candidates = strict_candidates if strict_candidates else broad_candidates
    if not candidates:
        return result

    result["candidate_count"] = int(len(candidates))
    top_k = min(10, len(candidates))
    ranked = matcher.rank_candidates(query_text, candidates, top_k=top_k)
    if not ranked:
        return result

    result["attempted"] = True
    result["ranked"] = ranked
    best = ranked[0]
    best_prob = float(best.get("match_probability", 0.0))
    second_prob = float(ranked[1].get("match_probability", 0.0)) if len(ranked) > 1 else 0.0
    prob_gap = best_prob - second_prob
    has_strict = bool(strict_candidates)

    result["best_probability"] = best_prob
    result["second_probability"] = second_prob
    result["probability_gap"] = prob_gap

    passes_threshold = (
        best_prob >= APP_REVISION_MATCH_THRESHOLD
        or (has_strict and best_prob >= max(0.0, APP_REVISION_MATCH_THRESHOLD - 0.08))
    )
    passes_gap = (len(ranked) == 1) or (prob_gap >= APP_REVISION_MATCH_MIN_GAP) or has_strict
    if not (passes_threshold and passes_gap):
        return result

    result["resolved"] = True
    result["target_idx"] = int(best.get("candidate_index", -1))
    return result


def _extract_update_payloads(message_text):
    txt = normalize_field_labels_in_text(message_text or "")
    txt_lower = txt.lower()
    is_revision = bool(re.search(r"\b(?:rev|revisi|update|ubah|ganti)\b", txt_lower))
    common_origin = normalize_origin(extract_origin_from_text(txt))
    common_route = normalize_route(extract_route_from_text(txt))
    common_unit = normalize_unit_type(extract_unit_type_from_text(txt))
    common_ro_date = extract_ro_date_from_text(txt).strip()

    payloads = []
    loading_details = extract_loading_details(txt)
    for det in loading_details:
        updates = {}
        det_driver = clean_driver_name(det.get("driver", ""))
        det_plate = clean_plate_value(det.get("plate", ""))
        det_phone = normalize_phone_number(det.get("phone", ""))
        det_time = _revml_normalize_time(det.get("time", ""))
        det_date = str(det.get("date", "") or "").strip()

        if det_driver:
            updates["DRIVER"] = det_driver
        if det_plate:
            updates["PLATE"] = det_plate
        if det_phone:
            updates["PHONE"] = det_phone
        if det_time:
            updates["TIME"] = det_time
        if det_date:
            updates["DATE"] = det_date
        if common_origin:
            updates["ORIGIN"] = common_origin
        if common_route:
            updates["DESTINATION"] = common_route
        if common_unit:
            updates["UNIT_TYPE"] = common_unit
        if common_ro_date:
            updates["RO_DATE"] = common_ro_date

        if updates:
            payloads.append(
                {
                    "target_time": det_time,
                    "target_origin": common_origin,
                    "target_route": common_route,
                    "target_unit": common_unit,
                    "target_ro_date": common_ro_date,
                    "target_load_date": det_date,
                    "updates": updates,
                    "is_revision": is_revision,
                }
            )

    if payloads:
        return payloads

    fallback_updates = {}
    driver_match = re.search(r"(?im)^\s*(?:driver|pengemudi)(?:\s*\d+)?\s*[:.]?\s*([^\n\r]+)", txt)
    if driver_match:
        driver_val = clean_driver_name(driver_match.group(1))
        if driver_val:
            fallback_updates["DRIVER"] = driver_val

    plate_match = re.search(r"(?im)^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*[:.]?\s*([^\n\r]+)", txt)
    if plate_match:
        plate_val = clean_plate_value(plate_match.group(1))
        if plate_val:
            fallback_updates["PLATE"] = plate_val

    phone_match = re.search(r"(?im)^\s*(?:no\.?\s*hp|hp|no\.?\s*telp|no\.?\s*tlp|kontak)\s*[:.]?\s*([^\n\r]+)", txt)
    if phone_match:
        phone_val = normalize_phone_number(phone_match.group(1))
        if phone_val:
            fallback_updates["PHONE"] = phone_val

    time_match = re.search(r"(?i)(?:jam|pukul|waktu(?:\s+loading)?)\s*:?\s*([^\n\r]+)", txt)
    target_time = ""
    target_load_date = ""
    if time_match:
        time_raw = time_match.group(1).strip()
        inline_time = re.search(r"(?i)^\s*(\d{1,2}[:.]\d{2})\s*(?:/|\s+)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})?", time_raw)
        if inline_time:
            target_time = _revml_normalize_time(inline_time.group(1))
            target_load_date = str(inline_time.group(2) or "").strip()
        else:
            target_time = _revml_normalize_time(time_raw)

    if target_time:
        fallback_updates["TIME"] = target_time
    if target_load_date:
        fallback_updates["DATE"] = target_load_date
    if common_origin:
        fallback_updates["ORIGIN"] = common_origin
    if common_route:
        fallback_updates["DESTINATION"] = common_route
    if common_unit:
        fallback_updates["UNIT_TYPE"] = common_unit
    if common_ro_date:
        fallback_updates["RO_DATE"] = common_ro_date

    if fallback_updates:
        return [
            {
                "target_time": target_time,
                "target_origin": common_origin,
                "target_route": common_route,
                "target_unit": common_unit,
                "target_ro_date": common_ro_date,
                "target_load_date": target_load_date,
                "updates": fallback_updates,
                "is_revision": is_revision,
            }
        ]

    return []


# --- [ML DOMINANT] REVISION + REFILL PARTIAL ---
def apply_revisions_from_chat(chat_text, df_final):
    if df_final is None or df_final.empty or not chat_text:
        return df_final

    matcher = _get_revision_matcher()
    if matcher is None:
        if APP_REVISION_RULE_FALLBACK_ENABLED:
            return _apply_revisions_from_chat_rule_engine(chat_text, df_final)
        return df_final

    event_classifier = _get_event_classifier()
    df = df_final.copy().reset_index(drop=True)
    messages = _split_wa_messages(chat_text)
    fallback_messages = []
    revision_mask = pd.Series(False, index=df.index)
    if "Original_Text" in df.columns:
        revision_mask = df["Original_Text"].apply(
            lambda x: bool(re.search(r"(?i)\b(?:rev|revisi|update)\b", str(x)))
        )

    for message in messages:
        message_str = str(message or "").strip()
        if not message_str:
            continue

        event_label, event_score = _predict_update_event(message_str, event_classifier)
        has_update_keyword = bool(
            re.search(
                r"(?i)\b(?:rev|revisi|update|ubah|ganti|ulang|tambahan|perbaikan|refill)\b",
                message_str,
            )
        )
        is_update_event = (event_label == "UPDATE" and event_score >= APP_EVENT_THRESHOLD) or has_update_keyword
        if not is_update_event:
            continue

        payloads = _extract_update_payloads(message_str)
        if not payloads:
            if APP_REVISION_RULE_FALLBACK_ENABLED:
                fallback_messages.append(message_str)
            continue

        source_indices = []
        if "Original_Text" in df.columns:
            msg_norm = _normalize_message_text(message_str)
            source_indices = [
                idx
                for idx in df.index
                if _normalize_message_text(df.at[idx, "Original_Text"]) == msg_norm
            ]
        source_index_set = set(source_indices)
        reserved_targets = set()
        message_applied = False

        for payload in payloads:
            updates = payload.get("updates", {}) or {}
            if not updates:
                continue

            is_revision = bool(payload.get("is_revision", False))
            mode = "REVISION" if is_revision else "REFILL"
            query_text = f"{message_str}\n{_build_match_query_text(payload)}".strip()
            if not query_text:
                continue

            strict_candidates = []
            broad_candidates = []
            for idx in df.index:
                if bool(revision_mask.loc[idx]):
                    continue
                if idx in source_index_set or idx in reserved_targets:
                    continue
                row = df.loc[idx]
                if mode == "REFILL" and not _row_needs_refill(row):
                    continue
                candidate_item = {
                    "candidate_index": int(idx),
                    "candidate_text": _build_match_candidate_text(row),
                }
                broad_candidates.append(candidate_item)
                if _revision_payload_context_compatible(payload, row):
                    strict_candidates.append(candidate_item)

            candidates = strict_candidates if strict_candidates else broad_candidates
            if not candidates:
                continue

            top_k = min(10, len(candidates))
            ranked = matcher.rank_candidates(query_text, candidates, top_k=top_k)
            if not ranked:
                continue

            best = ranked[0]
            best_prob = float(best.get("match_probability", 0.0))
            second_prob = float(ranked[1].get("match_probability", 0.0)) if len(ranked) > 1 else 0.0
            prob_gap = best_prob - second_prob
            has_strict = bool(strict_candidates)

            passes_threshold = (
                best_prob >= APP_REVISION_MATCH_THRESHOLD
                or (has_strict and best_prob >= max(0.0, APP_REVISION_MATCH_THRESHOLD - 0.08))
            )
            passes_gap = (len(ranked) == 1) or (prob_gap >= APP_REVISION_MATCH_MIN_GAP) or has_strict
            if not (passes_threshold and passes_gap):
                continue

            target_idx = int(best.get("candidate_index", -1))
            if target_idx not in df.index:
                continue
            if has_strict and not _revision_payload_context_compatible(payload, df.loc[target_idx]):
                continue

            changed = False
            handled = False
            for field, raw_value in updates.items():
                if field not in df.columns:
                    continue
                value = str(raw_value or "").strip()
                if not value:
                    continue

                if field == "DRIVER":
                    value = clean_driver_name(value)
                elif field == "PLATE":
                    value = clean_plate_value(value)
                elif field == "PHONE":
                    value = normalize_phone_number(value)
                elif field == "ORIGIN":
                    value = normalize_origin(value)
                elif field == "DESTINATION":
                    value = normalize_route(value)
                elif field == "UNIT_TYPE":
                    value = normalize_unit_type(value)
                elif field == "TIME":
                    value = _revml_normalize_time(value)
                elif field in {"DATE", "RO_DATE"}:
                    value = value.strip()

                if not value:
                    continue

                current = str(df.at[target_idx, field] or "").strip()
                if mode == "REVISION":
                    handled = True
                    if current != value:
                        df.at[target_idx, field] = value
                        changed = True
                else:
                    if not current:
                        df.at[target_idx, field] = value
                        changed = True
                        handled = True
                    elif current == value:
                        handled = True

            if handled:
                message_applied = True
                reserved_targets.add(target_idx)

        if not message_applied and APP_REVISION_RULE_FALLBACK_ENABLED:
            fallback_messages.append(message_str)

    if fallback_messages and APP_REVISION_RULE_FALLBACK_ENABLED:
        fallback_chat = "\n".join(fallback_messages)
        df = _apply_revisions_from_chat_rule_engine(fallback_chat, df)

    return df

def format_date_custom(date_input):
    try:
        if pd.isna(date_input) or str(date_input).strip() == "":
            return ""

        date_str = str(date_input).strip()
        date_str = re.sub(r'[^\w\s/\-]', ' ', date_str)
        date_str = re.sub(r'\s+', ' ', date_str).strip()
        if not date_str:
            return ""

        # Antisipasi jika TIME masih ikut di kolom DATE (contoh: "22:00 09 feb")
        time_prefix = re.search(r'^\d{1,2}[:.]\d{2}\s+(.+)$', date_str)
        if time_prefix:
            date_str = time_prefix.group(1).strip()

        current_year = datetime.now().year
        indo_months = {
            1: 'JANUARI', 2: 'FEBRUARI', 3: 'MARET', 4: 'APRIL',
            5: 'MEI', 6: 'JUNI', 7: 'JULI', 8: 'AGUSTUS',
            9: 'SEPTEMBER', 10: 'OKTOBER', 11: 'NOVEMBER', 12: 'DESEMBER'
        }
        month_map = {
            'januari': 1, 'january': 1, 'jan': 1,
            'februari': 2, 'february': 2, 'febuary': 2, 'febuari': 2, 'pebruari': 2, 'feb': 2, 'peb': 2,
            'maret': 3, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'mei': 5, 'may': 5,
            'juni': 6, 'june': 6, 'jun': 6,
            'juli': 7, 'july': 7, 'jul': 7,
            'agustus': 8, 'august': 8, 'agu': 8, 'aug': 8,
            'september': 9, 'sept': 9, 'sep': 9,
            'oktober': 10, 'october': 10, 'okt': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'desember': 12, 'december': 12, 'des': 12, 'dec': 12
        }

        def normalize_year(year_token):
            if year_token is None or str(year_token).strip() == "":
                return current_year
            token = str(year_token).strip()
            y = int(token)
            if len(token) == 2:
                base_century = (current_year // 100) * 100
                y = base_century + y
                if y > current_year + 50:
                    y -= 100
                elif y < current_year - 50:
                    y += 100
            return y

        day, month, year = None, None, None

        # Format numerik: DD/MM[/YY|YYYY] atau DD-MM[/YY|YYYY]
        match_digit = re.search(r'\b(\d{1,2})\s*[/\-]\s*(\d{1,2})(?:\s*[/\-]\s*(\d{2,4}))?\b', date_str)
        if match_digit:
            day = int(match_digit.group(1))
            month = int(match_digit.group(2))
            year = normalize_year(match_digit.group(3))
        else:
            clean_str = date_str.lower()
            month_match = None
            for k in sorted(month_map.keys(), key=len, reverse=True):
                m = re.search(rf'\b{re.escape(k)}\b', clean_str)
                if m:
                    month_match = m
                    month = month_map[k]
                    break

            if month_match:
                month_pos = month_match.start()
                all_numbers = [(m.start(), m.group(1)) for m in re.finditer(r'\b(\d{1,4})\b', clean_str)]

                day_candidates = [n for pos, n in all_numbers if pos < month_pos and len(n) <= 2]
                if day_candidates:
                    day = int(day_candidates[-1])

                year_candidates = [n for pos, n in all_numbers if pos > month_pos and len(n) in (2, 4)]
                if year_candidates:
                    year = normalize_year(year_candidates[0])
                else:
                    year = current_year

        if day and month and year and 1 <= day <= 31 and 1 <= month <= 12:
            return f"{day:02d} {indo_months[month]} {year}"
        return date_str
    except: return str(date_input)

def parse_date_custom(date_input):
    try:
        formatted = format_date_custom(date_input)
        if not formatted:
            return pd.NaT
        parts = str(formatted).strip().split()
        if len(parts) < 3:
            return pd.NaT
        day = int(parts[0])
        month_name = parts[1].lower()
        year = int(parts[2])
        month_map = {
            'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
        }
        month = month_map.get(month_name)
        if not month:
            return pd.NaT
        return pd.Timestamp(datetime(year, month, day))
    except:
        return pd.NaT

def clean_destination_format(text):
    if pd.isna(text): return ""
    return normalize_route(text)

def office_df_to_parser_rows(df_office):
    if df_office is None or df_office.empty:
        return []
    rows = []
    for _, row in df_office.iterrows():
        rows.append({
            "job_number": str(row.get("Job Number", "") or "").strip(),
            "tgl_ro": str(row.get("Tgl RO", "") or "").strip(),
            "tgl_muat": str(row.get("Tgl Muat", "") or "").strip(),
            "pickup": str(row.get("Pickup", "") or "").strip(),
            "tujuan": str(row.get("Tujuan", "") or "").strip(),
            "no_plat": str(row.get("No. Plat", "") or "").strip(),
            "type_truck": str(row.get("Type Truck", "") or "").strip(),
            "driver": str(row.get("Driver", "") or "").strip(),
            "kontak_driver": str(row.get("Kontak Driver", "") or "").strip(),
            "status_unit": str(row.get("status_unit", "") or "").strip(),
        })
    return rows


def parser_rows_to_office_df(rows):
    if not rows:
        return pd.DataFrame()

    df_office = pd.DataFrame(rows)
    rename_map = {
        "job_number": "Job Number",
        "tgl_ro": "Tgl RO",
        "tgl_muat": "Tgl Muat",
        "pickup": "Pickup",
        "tujuan": "Tujuan",
        "no_plat": "No. Plat",
        "type_truck": "Type Truck",
        "driver": "Driver",
        "kontak_driver": "Kontak Driver",
        "status_unit": "status_unit",
    }
    df_office = df_office.rename(columns=rename_map)

    required_cols = [
        "Job Number", "Tgl RO", "Tgl Muat", "Pickup", "Tujuan",
        "No. Plat", "Type Truck", "Driver", "Kontak Driver", "status_unit"
    ]

    for col in required_cols:
        if col not in df_office.columns:
            df_office[col] = ""

    df_office = df_office[required_cols]

    # Sorting konsisten dengan output utama: prioritas Tgl RO lalu Tgl Muat.
    df_office["_sort_muat"] = df_office["Tgl Muat"].apply(parse_date_custom)
    df_office["_sort_ro"] = df_office["Tgl RO"].apply(parse_date_custom)
    df_office = df_office.sort_values(by=["_sort_ro", "_sort_muat"], na_position='last').reset_index(drop=True)
    df_office = df_office.drop(columns=["_sort_muat", "_sort_ro"])
    df_office.insert(0, "No.", range(1, len(df_office) + 1))
    return df_office


def load_df_office_from_db():
    if not DB_PERSISTENCE_ENABLED or db_load_all_order_rows is None:
        return None
    try:
        rows = db_load_all_order_rows()
    except Exception:
        return None
    if not rows:
        return pd.DataFrame()
    return parser_rows_to_office_df(rows)


def calculate_extraction_accuracy(df_raw, df_final):
    if df_final is None or df_final.empty:
        return 0.0

    def _has_value(val):
        if val is None:
            return False
        s = str(val).strip()
        if not s:
            return False
        if s.lower() in {"-", "none", "null", "nan", "nat", "undefined"}:
            return False
        return True

    total_fields = 8 * len(df_final)
    filled_fields = 0

    for _, row in df_final.iterrows():
        ro_date = str(row.get("RO_DATE", "")).strip() or str(row.get("DATE", "")).strip()
        load_date = (
            str(row.get("DATE", "")).strip()
            or str(row.get("LOAD_DATE", "")).strip()
            or str(row.get("RO_DATE", "")).strip()
        )
        eval_values = [
            ro_date,                         # TGL_RO
            load_date,                       # TGL_MUAT
            row.get("ORIGIN", ""),         # PICKUP
            row.get("DESTINATION", ""),    # TUJUAN
            row.get("PLATE", ""),          # NO.PLAT
            row.get("UNIT_TYPE", ""),      # TYPE TRUCK
            row.get("DRIVER", ""),         # DRIVER
            row.get("PHONE", ""),          # KONTAK_DRIVER
        ]
        filled_fields += sum(1 for v in eval_values if _has_value(v))

    accuracy = round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0.0
    return min(accuracy, 100.0)


def _safe_div(a, b):
    return (float(a) / float(b)) if b else 0.0


def _normalize_time_metric(value):
    if value is None:
        return ""
    s = str(value).strip().upper().replace(".", ":")
    if not s:
        return ""
    if "SEGERA" in s:
        return "SEGERA"
    m = re.search(r'(\d{1,2})(?::(\d{2}))?', s)
    if not m:
        return ""
    hh = int(m.group(1))
    mm = m.group(2) if m.group(2) else "00"
    return f"{hh:02d}:{mm}"


def _normalize_date_metric(value):
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    parsed = parse_date_custom(s)
    if pd.notna(parsed):
        return str(parsed.date())
    return re.sub(r'[^A-Z0-9]+', '', s.upper())


def _normalize_plate_metric(value):
    plate = clean_plate_value(value)
    return re.sub(r'[^A-Z0-9]+', '', str(plate).upper())


def _normalize_route_metric(value):
    return normalize_route(value)


def _normalize_origin_metric(value):
    return normalize_origin(value)


def _normalize_unit_metric(value):
    return normalize_unit_type(value)


def _normalize_driver_metric(value):
    return clean_driver_name(value).upper()


def _extract_phone_candidates(value):
    if value is None:
        return []
    raw = str(value)
    seqs = re.findall(r'\+?\d[\d\-\s]{6,}', raw)
    nums = [normalize_phone_number(x) for x in seqs]
    nums = [n for n in nums if n]
    if not nums:
        one = normalize_phone_number(raw)
        if one:
            nums = [one]
    unique = []
    seen = set()
    for n in nums:
        if n in seen:
            continue
        seen.add(n)
        unique.append(n)
    return unique


def _extract_driver_candidates(value):
    if value is None:
        return []
    raw = str(value)
    parts = [x.strip() for x in re.split(r'\s*&\s*|,|/|;', raw) if x.strip()]
    names = [_normalize_driver_metric(x) for x in parts]
    names = [n for n in names if n]
    if not names:
        single = _normalize_driver_metric(raw)
        if single:
            names = [single]
    unique = []
    seen = set()
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        unique.append(n)
    return unique


def _field_match(field, pred_value, exp_value):
    if not str(exp_value or "").strip():
        return False

    if field == "PHONE":
        pred_nums = _extract_phone_candidates(pred_value)
        exp_num = normalize_phone_number(exp_value)
        return bool(exp_num and exp_num in pred_nums)

    if field == "DRIVER":
        pred_names = _extract_driver_candidates(pred_value)
        exp_name = _normalize_driver_metric(exp_value)
        return bool(exp_name and exp_name in pred_names)

    if field == "PLATE":
        exp_norm = _normalize_plate_metric(exp_value)
        if not exp_norm:
            return False
        pred_text = str(pred_value or "")
        pred_parts = [x.strip() for x in re.split(r'\s*&\s*|,|/|;', pred_text) if x.strip()]
        pred_norms = [_normalize_plate_metric(x) for x in pred_parts]
        if not pred_norms:
            pred_norms = [_normalize_plate_metric(pred_text)]
        return exp_norm in [p for p in pred_norms if p]

    if field == "TIME":
        return _normalize_time_metric(pred_value) == _normalize_time_metric(exp_value)

    if field == "DATE":
        return _normalize_date_metric(pred_value) == _normalize_date_metric(exp_value)

    if field == "ORIGIN":
        return _normalize_origin_metric(pred_value) == _normalize_origin_metric(exp_value)

    if field == "DESTINATION":
        return _normalize_route_metric(pred_value) == _normalize_route_metric(exp_value)

    if field == "UNIT_TYPE":
        return _normalize_unit_metric(pred_value) == _normalize_unit_metric(exp_value)

    return str(pred_value or "").strip().upper() == str(exp_value or "").strip().upper()


def _field_equal(field, left_value, right_value):
    if field == "PHONE":
        left = sorted(_extract_phone_candidates(left_value))
        right = sorted(_extract_phone_candidates(right_value))
        return left == right

    if field == "DRIVER":
        left = sorted(_extract_driver_candidates(left_value))
        right = sorted(_extract_driver_candidates(right_value))
        return left == right

    if field == "PLATE":
        left = _normalize_plate_metric(left_value)
        right = _normalize_plate_metric(right_value)
        return left == right

    if field == "TIME":
        return _normalize_time_metric(left_value) == _normalize_time_metric(right_value)

    if field == "DATE":
        return _normalize_date_metric(left_value) == _normalize_date_metric(right_value)

    if field == "ORIGIN":
        return _normalize_origin_metric(left_value) == _normalize_origin_metric(right_value)

    if field == "DESTINATION":
        return _normalize_route_metric(left_value) == _normalize_route_metric(right_value)

    if field == "UNIT_TYPE":
        return _normalize_unit_metric(left_value) == _normalize_unit_metric(right_value)

    return str(left_value or "").strip().upper() == str(right_value or "").strip().upper()


def _extract_expected_from_original_text(original_text):
    text = normalize_field_labels_in_text(original_text or "")

    expected = {
        "RO_DATE": "",
        "LOAD_DATE": "",
        "ORIGIN": _normalize_origin_metric(extract_origin_from_text(text)),
        "DESTINATION": _normalize_route_metric(extract_route_from_text(text)),
        "UNIT_TYPE": _normalize_unit_metric(extract_unit_type_from_text(text)),
        "TIME": "",
        "DATE": "",
        "DRIVER": "",
        "PLATE": "",
        "PHONE": "",
    }

    ro_date = extract_ro_date_from_text(text)
    if ro_date:
        expected["RO_DATE"] = _normalize_date_metric(ro_date)
        expected["LOAD_DATE"] = expected["RO_DATE"]

    loading_details = extract_loading_details(text)
    if loading_details:
        first = loading_details[0]
        expected["TIME"] = _normalize_time_metric(first.get("time", ""))
        expected["DATE"] = str(first.get("date", "")).strip()
        expected["DRIVER"] = clean_driver_name(first.get("driver", ""))
        expected["PLATE"] = clean_plate_value(first.get("plate", ""))
        expected["PHONE"] = normalize_phone_number(first.get("phone", ""))

    if not expected["TIME"] or not expected["DATE"]:
        loading_candidates = extract_loading_candidates(text)
        if loading_candidates:
            first_c = loading_candidates[0]
            if not expected["TIME"]:
                expected["TIME"] = _normalize_time_metric(first_c.get("time", ""))
            if not expected["DATE"]:
                expected["DATE"] = str(first_c.get("date", "")).strip()

    if not expected["DRIVER"]:
        driver_match = re.search(
            r'(?im)^\s*(?:driver|pengemudi)(?:\s*\d+)?\s*[:.]?\s*([^\n\r]*)',
            text,
        )
        if driver_match:
            expected["DRIVER"] = clean_driver_name(driver_match.group(1))

    if not expected["PLATE"]:
        plate_match = re.search(
            r'(?im)^\s*(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*[:.]?\s*([^\n\r]*)',
            text,
        )
        if plate_match:
            expected["PLATE"] = clean_plate_value(plate_match.group(1))
        else:
            expected["PLATE"] = clean_plate_value(extract_plate_aggressive(text))

    if not expected["PHONE"]:
        phones = extract_phone_numbers_from_text(text)
        if phones:
            expected["PHONE"] = phones[0]

    if expected["DATE"]:
        expected["DATE"] = _normalize_date_metric(expected["DATE"])
        expected["LOAD_DATE"] = expected["DATE"]

    return expected


def _score_from_counts(tp, fp, fn):
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    accuracy = _safe_div(tp, tp + fp + fn)
    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def compute_ner_business_scores(df_final):
    field_specs = [
        {"label": "TGL_RO", "pred_cols": ["RO_DATE", "DATE"], "exp_key": "RO_DATE", "match_key": "DATE"},
        {"label": "TGL_MUAT", "pred_cols": ["DATE", "LOAD_DATE", "RO_DATE"], "exp_key": "LOAD_DATE", "match_key": "DATE"},
        {"label": "PICKUP", "pred_cols": ["ORIGIN"], "exp_key": "ORIGIN", "match_key": "ORIGIN"},
        {"label": "TUJUAN", "pred_cols": ["DESTINATION"], "exp_key": "DESTINATION", "match_key": "DESTINATION"},
        {"label": "NO.PLAT", "pred_cols": ["PLATE"], "exp_key": "PLATE", "match_key": "PLATE"},
        {"label": "TYPE TRUCK", "pred_cols": ["UNIT_TYPE"], "exp_key": "UNIT_TYPE", "match_key": "UNIT_TYPE"},
        {"label": "DRIVER", "pred_cols": ["DRIVER"], "exp_key": "DRIVER", "match_key": "DRIVER"},
        {"label": "KONTAK_DRIVER", "pred_cols": ["PHONE"], "exp_key": "PHONE", "match_key": "PHONE"},
    ]

    if df_final is None or df_final.empty:
        return {
            "summary": {**_score_from_counts(0, 0, 0), "rows": 0, "evaluable_cells": 0},
            "field_metrics": [],
        }

    labels = [spec["label"] for spec in field_specs]
    stats = {
        f: {"tp": 0, "fp": 0, "fn": 0, "support": 0}
        for f in labels
    }

    def _pick_first_non_empty(row, cols):
        for c in cols:
            v = row.get(c, "")
            if str(v or "").strip():
                return v
        return ""

    for _, row in df_final.iterrows():
        expected = _extract_expected_from_original_text(str(row.get("Original_Text", "") or ""))
        for spec in field_specs:
            label = spec["label"]
            exp = expected.get(spec["exp_key"], "")
            if not str(exp or "").strip():
                continue

            stats[label]["support"] += 1
            pred = _pick_first_non_empty(row, spec["pred_cols"])
            matched = _field_match(spec["match_key"], pred, exp)
            if matched:
                stats[label]["tp"] += 1
            else:
                if str(pred or "").strip():
                    stats[label]["fp"] += 1
                stats[label]["fn"] += 1

    rows = []
    total_tp = total_fp = total_fn = total_support = 0
    for spec in field_specs:
        label = spec["label"]
        st_f = stats[label]
        met = _score_from_counts(st_f["tp"], st_f["fp"], st_f["fn"])
        total_tp += st_f["tp"]
        total_fp += st_f["fp"]
        total_fn += st_f["fn"]
        total_support += st_f["support"]
        rows.append(
            {
                "field": label,
                "support": int(st_f["support"]),
                "tp": met["tp"],
                "fp": met["fp"],
                "fn": met["fn"],
                "accuracy": met["accuracy"],
                "precision": met["precision"],
                "recall": met["recall"],
                "f1": met["f1"],
            }
        )

    summary = _score_from_counts(total_tp, total_fp, total_fn)
    summary["rows"] = int(len(df_final))
    summary["evaluable_cells"] = int(total_support)
    return {
        "summary": summary,
        "field_metrics": rows,
    }


def _extract_revision_payload_for_metrics(msg_text):
    msg_text = normalize_field_labels_in_text(msg_text or "")
    payload = {
        "target_time": None,
        "target_origin": "",
        "target_route": "",
        "target_unit": "",
        "updates": {},
    }

    time_match = re.search(r'(?i)(?:jam|pukul|waktu(?:\s+loading)?)\s*:?\s*(\d{1,2}(?:[:.]\d{2})?)', msg_text)
    if time_match:
        payload["target_time"] = _normalize_time_metric(time_match.group(1))

    lokasi_match = re.search(r'(?im)^\s*Lokasi\s*:\s*([^\n\r]+)', msg_text)
    if lokasi_match:
        payload["target_origin"] = str(lokasi_match.group(1)).strip().upper()

    route_match = re.search(r'(?im)^\s*Rute(?:\s*/\s*|\s+)tujuan\s*:\s*([^\n\r]+)', msg_text)
    if route_match:
        payload["target_route"] = normalize_route(route_match.group(1))

    unit_match = re.search(r'(?im)^\s*(?:jenis\s+unit|type\s+truck)\s*:\s*([^\n\r]+)', msg_text)
    if unit_match:
        payload["target_unit"] = normalize_unit_type(unit_match.group(1))

    for line in str(msg_text).split('\n'):
        line = line.strip()
        if not line:
            continue

        plate_match = re.search(
            r'(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:?\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})',
            line,
            re.IGNORECASE,
        )
        if plate_match:
            payload["updates"]["PLATE"] = plate_match.group(1).strip().upper()

        driver_match = re.search(r'(?:driver|pengemudi)\s*:?\s*([a-zA-Z.\s]+)', line, re.IGNORECASE)
        if driver_match:
            d_name = clean_driver_name(driver_match.group(1).strip())
            if d_name and not re.search(r'(?i)\b(?:rev|revisi|update)\b', d_name):
                payload["updates"]["DRIVER"] = d_name

        phone_match = re.search(r'(?:no\.?\s*hp|hp|no\.?\s*telp|kontak)\s*:?\s*([0-9+\-\s]+)', line, re.IGNORECASE)
        if phone_match:
            payload["updates"]["PHONE"] = normalize_phone_number(phone_match.group(1).strip())

    return payload


def compute_revision_business_scores(chat_text, df_before, df_after):
    base_summary = {
        "total_revision_messages": 0,
        "total_refill_messages": 0,
        "total_update_messages": 0,
        "messages_with_updates": 0,
        "total_payloads": 0,
        "total_revision_payloads": 0,
        "total_refill_payloads": 0,
        "matched_payloads": 0,
        "matched_revision_payloads": 0,
        "matched_refill_payloads": 0,
        "resolved_targets": 0,
        "target_hit": 0,
        "unintended_overwrites": 0,
        "ml_model_available": False,
        "ml_attempted_matches": 0,
        "ml_resolved_matches": 0,
        "ml_avg_best_probability": 0.0,
        "ml_avg_resolved_probability": 0.0,
        "ml_match_rate": 0.0,
        "revision_match_rate": 0.0,
        "refill_match_rate": 0.0,
    }
    empty_summary = {**base_summary, **_score_from_counts(0, 0, 0), "target_accuracy": 0.0}
    empty = {"summary": empty_summary, "field_metrics": []}
    if df_before is None or df_before.empty or df_after is None or df_after.empty or not chat_text:
        return empty

    matcher = _get_revision_matcher()
    base_summary["ml_model_available"] = bool(matcher is not None)
    if matcher is None:
        return {"summary": {**base_summary, **_score_from_counts(0, 0, 0), "target_accuracy": 0.0}, "field_metrics": []}

    event_classifier = _get_event_classifier()
    messages = _split_wa_messages(chat_text)
    fields = ["DRIVER", "PLATE", "PHONE"]
    field_stats = {f: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for f in fields}
    total_tp = total_fp = total_fn = 0

    revision_mask = pd.Series(False, index=df_before.index)
    if "Original_Text" in df_before.columns:
        revision_mask = df_before["Original_Text"].apply(lambda x: bool(re.search(r'(?i)\b(?:rev|revisi|update)\b', str(x))))

    ml_best_prob_sum = 0.0
    ml_resolved_prob_sum = 0.0

    def _count_unresolved_field_penalties(updates):
        nonlocal total_fn
        for field, _ in updates.items():
            if field not in field_stats:
                continue
            field_stats[field]["support"] += 1
            field_stats[field]["fn"] += 1
            total_fn += 1

    for msg in messages:
        message_str = str(msg or "").strip()
        if not message_str:
            continue

        is_update_event, _, _, _ = _is_update_event_message(message_str, event_classifier)
        if not is_update_event:
            continue

        payloads = _extract_update_payloads(message_str)
        payloads = [p for p in payloads if (p.get("updates") or {})]
        if not payloads:
            continue

        base_summary["total_update_messages"] += 1
        has_revision_payload = any(bool(p.get("is_revision", False)) for p in payloads)
        has_refill_payload = any(not bool(p.get("is_revision", False)) for p in payloads)
        if has_revision_payload:
            base_summary["total_revision_messages"] += 1
        if has_refill_payload:
            base_summary["total_refill_messages"] += 1

        base_summary["messages_with_updates"] += 1
        source_indices = []
        if "Original_Text" in df_before.columns:
            msg_norm = _normalize_message_text(message_str)
            source_indices = [
                idx
                for idx in df_before.index
                if _normalize_message_text(df_before.at[idx, "Original_Text"]) == msg_norm
            ]
        source_index_set = set(source_indices)
        reserved_targets = set()
        msg_hit = False

        for payload in payloads:
            updates = payload.get("updates", {}) or {}
            if not updates:
                continue

            mode = "REVISION" if bool(payload.get("is_revision", False)) else "REFILL"
            base_summary["total_payloads"] += 1
            if mode == "REVISION":
                base_summary["total_revision_payloads"] += 1
            else:
                base_summary["total_refill_payloads"] += 1

            query_text = f"{message_str}\n{_build_match_query_text(payload)}".strip()
            if not query_text:
                _count_unresolved_field_penalties(updates)
                continue

            strict_candidates, broad_candidates = _build_match_candidates_for_payload(
                df=df_before,
                payload=payload,
                mode=mode,
                revision_mask=revision_mask,
                source_index_set=source_index_set,
                reserved_targets=reserved_targets,
            )
            selection = _select_target_with_matcher(
                matcher=matcher,
                query_text=query_text,
                strict_candidates=strict_candidates,
                broad_candidates=broad_candidates,
            )
            if selection.get("attempted", False):
                base_summary["ml_attempted_matches"] += 1
                ml_best_prob_sum += float(selection.get("best_probability", 0.0))

            if not selection.get("resolved", False):
                _count_unresolved_field_penalties(updates)
                continue

            target_idx = int(selection.get("target_idx", -1))
            if target_idx not in df_before.index:
                _count_unresolved_field_penalties(updates)
                continue
            if selection.get("has_strict_context", False) and not _revision_payload_context_compatible(payload, df_before.loc[target_idx]):
                _count_unresolved_field_penalties(updates)
                continue

            base_summary["resolved_targets"] += 1
            base_summary["ml_resolved_matches"] += 1
            base_summary["matched_payloads"] += 1
            ml_resolved_prob_sum += float(selection.get("best_probability", 0.0))
            if mode == "REVISION":
                base_summary["matched_revision_payloads"] += 1
            else:
                base_summary["matched_refill_payloads"] += 1
            reserved_targets.add(target_idx)
            payload_hit = False
            updated_fields_effective = set()

            for field, expected_val in updates.items():
                if field not in field_stats:
                    continue

                expected_val = str(expected_val or "").strip()
                if not expected_val:
                    continue

                before_val = df_before.at[target_idx, field] if field in df_before.columns else ""
                after_val = df_after.at[target_idx, field] if field in df_after.columns else ""

                # REFILL hanya valid jika field memang kosong sebelumnya, atau sudah sama
                # (idempotent). Kalau berbeda tapi terubah, hitung sebagai overwrite.
                if mode == "REFILL":
                    before_blank = not str(before_val or "").strip()
                    before_same = _field_match(field, before_val, expected_val)
                    if not (before_blank or before_same):
                        if not _field_equal(field, before_val, after_val):
                            base_summary["unintended_overwrites"] += 1
                        continue

                field_stats[field]["support"] += 1
                changed = not _field_equal(field, before_val, after_val)
                matched = _field_match(field, after_val, expected_val)
                updated_fields_effective.add(field)

                if matched:
                    field_stats[field]["tp"] += 1
                    total_tp += 1
                    payload_hit = True
                else:
                    field_stats[field]["fn"] += 1
                    total_fn += 1
                    if changed:
                        field_stats[field]["fp"] += 1
                        total_fp += 1

            if payload_hit:
                msg_hit = True

            for side_field in fields:
                if side_field in updates:
                    continue
                if side_field in updated_fields_effective:
                    continue
                before_side = df_before.at[target_idx, side_field] if side_field in df_before.columns else ""
                after_side = df_after.at[target_idx, side_field] if side_field in df_after.columns else ""
                if not _field_equal(side_field, before_side, after_side):
                    base_summary["unintended_overwrites"] += 1

        if msg_hit:
            base_summary["target_hit"] += 1

    summary_scores = _score_from_counts(total_tp, total_fp, total_fn)
    target_accuracy = _safe_div(base_summary["target_hit"], base_summary["messages_with_updates"])
    base_summary["ml_avg_best_probability"] = _safe_div(ml_best_prob_sum, base_summary["ml_attempted_matches"])
    base_summary["ml_avg_resolved_probability"] = _safe_div(ml_resolved_prob_sum, base_summary["ml_resolved_matches"])
    base_summary["ml_match_rate"] = _safe_div(base_summary["ml_resolved_matches"], base_summary["ml_attempted_matches"])
    base_summary["revision_match_rate"] = _safe_div(
        base_summary["matched_revision_payloads"],
        base_summary["total_revision_payloads"],
    )
    base_summary["refill_match_rate"] = _safe_div(
        base_summary["matched_refill_payloads"],
        base_summary["total_refill_payloads"],
    )
    summary = {
        **base_summary,
        **summary_scores,
        "target_accuracy": target_accuracy,
    }

    field_rows = []
    for f in fields:
        met = _score_from_counts(field_stats[f]["tp"], field_stats[f]["fp"], field_stats[f]["fn"])
        field_rows.append(
            {
                "field": f,
                "support": int(field_stats[f]["support"]),
                "tp": met["tp"],
                "fp": met["fp"],
                "fn": met["fn"],
                "accuracy": met["accuracy"],
                "precision": met["precision"],
                "recall": met["recall"],
                "f1": met["f1"],
            }
        )

    return {"summary": summary, "field_metrics": field_rows}

# =================================================================================
# --- FRONTEND UI: WHITE THEME - PROFESSIONAL EDITION ---
# =================================================================================

st.set_page_config(page_title="", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-color: #ffffff;
            --bg-elev-1: #ffffff;
            --bg-elev-2: #f4f4f4;
            --card-bg: #ffffff;
            --border-color: #101010;
            --accent-color: #000000;
            --accent-strong: #000000;
            --text-main: #000000;
            --text-muted: #1f1f1f;
            --text-dim: #454545;
            --success-color: #000000;
            --warning-color: #000000;
        }
        
        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%) !important;
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: var(--text-main) !important;
        }

        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {
            visibility: visible !important;
            background: transparent !important;
        }
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            visibility: visible !important;
            display: flex !important;
            opacity: 1 !important;
        }
        footer {visibility: hidden;}
        .block-container { padding-top: 1.6rem !important; max-width: 1400px; }

        .top-navbar {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid var(--border-color); padding-bottom: 16px; margin-bottom: 22px;
        }
        .nav-logo { display: flex; align-items: center; gap: 14px; }
        .nav-title { font-size: 1.45rem; font-weight: 700; color: var(--text-main); margin: 0; line-height: 1.15; letter-spacing: 0.3px; }
        .nav-subtitle { font-size: 0.85rem; color: var(--text-muted); margin: 4px 0 0 0; font-weight: 500; }
        .nav-accent { color: var(--accent-color); font-weight: 700; }
        .nav-status { display: flex; gap: 14px; }
        .status-badge {
            background-color: var(--bg-elev-1); border: 1px solid var(--border-color);
            padding: 8px 14px; border-radius: 8px; font-size: 0.8rem; color: var(--text-muted);
            display: flex; align-items: center; gap: 8px; font-weight: 600;
            box-shadow: none;
        }
        .status-dot { width: 8px; height: 8px; background-color: var(--success-color); border-radius: 50%; box-shadow: none; }

        .input-panel {
            background-color: var(--bg-elev-1); border: 1px solid var(--border-color);
            border-radius: 10px; padding: 18px; height: 100%;
            box-shadow: none;
        }
        .input-panel-wide { padding: 16px 18px 12px 18px; }
        .panel-header { display: flex; align-items: center; gap: 10px; font-weight: 700; color: var(--text-main); margin-bottom: 12px; }
        .badge-ml { background-color: #f1f1f1; color: var(--accent-strong); font-size: 0.65rem; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border-color); font-weight: 600; }
        
        .tab-mockup { display: flex; gap: 8px; margin-bottom: 12px; }
        .tab-btn { background-color: var(--bg-elev-2); border: 1px solid var(--border-color); color: var(--text-main); padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; width: 50%; text-align: center; cursor: default; }
        .tab-inactive { background-color: transparent; color: var(--text-dim); border-style: dashed; }
        
        .stTextArea textarea {
            background-color: #ffffff !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important;
            border-radius: 8px !important; font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace !important;
            font-size: 0.82rem; padding: 14px; line-height: 1.5;
        }
        .stTextArea textarea:focus { border-color: var(--accent-color) !important; box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.12) !important;}
        
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input {
            background-color: #ffffff !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }

        div.stButton > button {
            background: #000000 !important; color: #ffffff !important; border: 1px solid #000000 !important;
            border-radius: 8px !important; padding: 11px 16px !important; font-weight: 700 !important; width: 100% !important; margin-top: 12px; transition: 0.2s;
            box-shadow: none;
        }
        div.stButton > button:hover { background: #1a1a1a !important; color: #ffffff !important; transform: translateY(-1px); box-shadow: none; }

        .output-panel {
            background-color: var(--bg-elev-1); border: 1px solid var(--border-color);
            border-radius: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 500px;
            box-shadow: none;
        }
        .out-icon { background-color: #f3f3f3; padding: 18px; border-radius: 14px; margin-bottom: 18px; position: relative; }
        .out-icon svg { width: 38px; color: var(--accent-color); }
        .out-badge { position: absolute; bottom: -6px; right: -6px; background: #ffffff; color: #000000; border: 1px solid #000000; font-size: 0.6rem; font-weight: 700; padding: 4px 8px; border-radius: 999px; }
        .out-title { color: var(--text-main); font-weight: 700; font-size: 1.15rem; margin-bottom: 8px; }
        .out-desc { color: var(--text-muted); font-size: 0.82rem; text-align: center; max-width: 420px; line-height: 1.6; margin-bottom: 24px; }
        
        .out-options { display: flex; gap: 12px; }
        .opt-box { background: var(--card-bg); border: 1px solid var(--border-color); padding: 10px 16px; border-radius: 8px; text-align: center; }
        .opt-box p { margin: 0; color: var(--text-main); font-weight: 600; font-size: 0.82rem; }
        .opt-box span { color: var(--text-dim); font-size: 0.7rem; display: block; margin-top: 2px; }
        .stat-control {
            width: 100%;
        }
        .stat-control-label {
            color: var(--text-main);
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.2;
            margin: 0 0 0.3rem 0;
        }
        .stat-chip {
            background-color: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px;
            height: 48px;
            width: 100%;
            box-sizing: border-box;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }
        .stat-chip-label {
            color: var(--text-main);
            font-size: 0.84rem;
            font-weight: 600;
            margin: 0;
            line-height: 1.1;
        }
        .stat-chip-value {
            color: var(--accent-strong);
            font-size: 1rem;
            font-weight: 700;
            line-height: 1;
            margin: 0;
        }

        [data-testid="stDataFrame"] { background-color: var(--bg-elev-1) !important; }
        .stDataFrame { background-color: var(--bg-elev-1) !important; }
        [data-testid="stDataFrame"] > div { background-color: var(--bg-elev-1) !important; }
        [data-testid="stDataFrame"] tbody td { color: #000000 !important; background-color: #ffffff; border-color: var(--border-color) !important; }
        [data-testid="stDataFrame"] thead th { background-color: #efefef !important; color: var(--text-main) !important; border-color: var(--border-color) !important; font-weight: 600; }
        [data-testid="stDataFrame"] tbody tr:nth-child(odd) { background-color: #ffffff !important; }
        [data-testid="stDataFrame"] tbody tr:nth-child(even) { background-color: #f8f8f8 !important; }
        [data-testid="stDataFrame"] table { border-color: var(--border-color) !important; border-collapse: collapse; }
        [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td { border-color: var(--border-color) !important; padding: 10px 12px; }
        [data-testid="stDataFrame"] tbody tr:hover { background-color: rgba(0, 0, 0, 0.08) !important; }
        
        div.stDownloadButton > button { background: #ffffff !important; color: #000000 !important; border: 1px solid #000000 !important; border-radius: 8px !important; font-weight: 700 !important; width: 100% !important; margin-top: 12px; box-shadow: none; }
        div.stDownloadButton > button:hover { background: #efefef !important; box-shadow: none; }

        .result-container { background-color: var(--bg-elev-1); padding: 22px; border-radius: 10px; border: 1px solid var(--border-color); box-shadow: none; }
        .result-header { color: var(--text-main); font-weight: 700; font-size: 1rem; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }

        .dashboard-container { width: 100%; margin-bottom: 16px; }
        .metric-box { background-color: #000000; border: 1px solid #000000; border-radius: 10px; padding: 18px; text-align: center; box-shadow: none; }
        .metric-box-label { font-size: 0.7rem; font-weight: 600; color: #ffffff; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
        .metric-box-value { font-size: 1.6rem; font-weight: 700; color: #ffffff; line-height: 1.2; }

        .muted-preview { font-size: 0.86rem; color: var(--text-muted); }
        .processing-box { background-color: var(--bg-elev-1); border: 1px solid var(--border-color); border-radius: 10px; padding: 22px; box-shadow: none; }
        .processing-title { font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 12px; }
        .section-spacer { height: 14px; }
        .full-width { width: 100%; }

        .stMarkdown p, .stMarkdown li, .stMarkdown span { color: var(--text-main); }
        .stMarkdown small, .stMarkdown .caption { color: var(--text-muted); }
        code, pre { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace !important; }
        .stAlert, .stInfo, .stWarning, .stSuccess { border-radius: 10px; }

        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #000000 !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #ffffff !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
        }
        section[data-testid="stSidebar"] h3 {
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
            margin-bottom: 0.4rem !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            border: 1px solid #000000;
            border-radius: 10px;
            overflow: hidden;
            background: #ffffff;
        }
        section[data-testid="stSidebar"] label[data-baseweb="radio"] {
            margin: 0 !important;
            padding: 0 !important;
            border-bottom: 1px solid #000000;
            background: #ffffff;
        }
        section[data-testid="stSidebar"] label[data-baseweb="radio"]:last-child {
            border-bottom: none;
        }
        section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {
            display: none !important;
        }
        section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:last-child {
            width: 100%;
            padding: 11px 12px;
            color: #000000 !important;
            font-weight: 600;
            line-height: 1.2;
        }
        section[data-testid="stSidebar"] label[data-baseweb="radio"][aria-checked="true"] > div:last-child {
            background: #000000;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_processor(
    split_version="split_v3_multi_unit",
    model_path_override="",
    event_model_path_override="",
    event_threshold=0.75,
):
    # Argumen versi dipakai untuk memastikan cache ter-refresh saat logika split berubah.
    model_path = Path(model_path_override) if model_path_override else None
    event_model_path = event_model_path_override if event_model_path_override else None
    return ChatBatchProcessor(
        model_path=model_path,
        event_model_path=event_model_path,
        event_threshold=event_threshold,
    )

def _get_query_param_value(param_name, default_value):
    try:
        value = st.query_params.get(param_name, default_value)
    except Exception:
        legacy_params = st.experimental_get_query_params()
        value = legacy_params.get(param_name, [default_value])

    if isinstance(value, list):
        return str(value[0]) if value else str(default_value)
    return str(value)

def _resolve_page_from_query():
    raw_page = _get_query_param_value("page", "ekstraksi").strip().lower()
    if raw_page in {"dashboard", "audit", "audit_dashboard"}:
        return "dashboard"
    return "ekstraksi"

def _navigate_to_page(page_name):
    """Update query params to navigate to the specified page"""
    try:
        st.query_params["page"] = page_name
    except Exception:
        # Fallback untuk versi Streamlit yang lebih lama
        st.experimental_set_query_params(page=page_name)

def _render_sidebar_navigation(active_page):
    current = "Ekstraksi Data" if active_page == "ekstraksi" else "Dashboard Evaluasi"
    st.sidebar.markdown("### Navigasi Utama")
    selected = st.sidebar.radio(
        "Navigasi Utama",
        options=["Ekstraksi Data", "Dashboard Evaluasi"],
        index=0 if current == "Ekstraksi Data" else 1,
        label_visibility="collapsed",
    )

    target_page = "ekstraksi" if selected == "Ekstraksi Data" else "dashboard"
    if target_page != active_page:
        _navigate_to_page(target_page)
        st.rerun()

def _render_audit_dashboard_page():
    try:
        from db.database import engine
        from audit_dashboard import render_batch_audit_feed
    except Exception as e:
        st.error(f"Gagal memuat dashboard audit: {e}")
        return

    render_batch_audit_feed(engine)

def main():
    if 'waktu' not in st.session_state: st.session_state.waktu = "--"
    if 'baris' not in st.session_state: st.session_state.baris = "--"
    if 'processing_time' not in st.session_state: st.session_state.processing_time = 0.0

    active_page = _resolve_page_from_query()
    _render_sidebar_navigation(active_page)
    if active_page == "dashboard":
        _render_audit_dashboard_page()
        return

    if 'db_bootstrap_done' not in st.session_state:
        st.session_state['db_bootstrap_done'] = True
        if DB_PERSISTENCE_ENABLED and db_init_db is not None:
            try:
                db_init_db()
            except Exception:
                pass

    if 'df_office' not in st.session_state and DB_PERSISTENCE_ENABLED:
        df_saved = load_df_office_from_db()
        if df_saved is not None and not df_saved.empty:
            st.session_state['df_office'] = df_saved
            st.session_state.baris = f"{len(df_saved)} Order"
    
    
    st.markdown("""
    
    """, unsafe_allow_html=True)

    st.markdown("**Konfigurasi Job Number**")
    col_job1, col_job2, col_job3, col_job4 = st.columns(4, gap="small")

    with col_job1:
        job_start = st.number_input("Nomor", value=st.session_state.get('job_start', 1), min_value=1, step=1)
        st.session_state['job_start'] = job_start

    with col_job2:
        job_company = st.text_input("Company", value=st.session_state.get('job_company', 'JNE'), max_chars=6)
        st.session_state['job_company'] = job_company.upper()

    with col_job3:
        month_options = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        month_idx = month_options.index(st.session_state.get('job_month', 'II')) if st.session_state.get('job_month', 'II') in month_options else 1
        job_month = st.selectbox("Bulan", month_options, index=month_idx)
        st.session_state['job_month'] = job_month

    with col_job4:
        job_year = st.number_input("Tahun", value=st.session_state.get('job_year', 2026), min_value=2000, max_value=2100, step=1)
        st.session_state['job_year'] = job_year

    effective_start = job_start
    preview_format = f"{effective_start:03d}/{job_company.upper()}-RAFAY/{job_month}/{job_year}"
    st.markdown(f"<span class='muted-preview'>Preview: <code>{preview_format}</code></span>", unsafe_allow_html=True)

    chat_input = st.text_area(
        "Input", height=260, label_visibility="collapsed",
        placeholder="Paste data chat WhatsApp atau dokumen logistik di sini..."
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1], gap="small")
    with btn_col1:
        btn = st.button("Mulai Ekstraksi Data")
    with btn_col3:
        btn_reset_db = st.button("Reset DB ke 0")


    if btn_reset_db:
        st.session_state.pop('df_office', None)
        st.session_state.waktu = "--"
        st.session_state.baris = "--"
        st.session_state.processing_time = 0.0

        if not DB_PERSISTENCE_ENABLED or db_reset_all_data is None:
            st.warning("Mode database tidak aktif. Hanya output lokal yang dihapus.")
            st.rerun()

        try:
            reset_info = db_reset_all_data()
        except Exception:
            st.error("Gagal reset database. Cek koneksi DB lalu coba lagi.")
        else:
            order_deleted = reset_info.get("order_dataset_deleted", 0)
            raw_deleted = reset_info.get("raw_chats_deleted", 0)
            st.success(f"Database berhasil direset ke 0 data (order_dataset: {order_deleted} baris, raw_chats: {raw_deleted} baris).")
            st.rerun()

    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)

    if not btn and 'df_office' not in st.session_state:
        st.markdown("""
        <div class="output-panel full-width">
            <div class="out-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <div class="out-badge">AI</div>
            </div>
            <div class="out-title">Siap Memproses Data</div>
        </div>
        """, unsafe_allow_html=True)
        
    if btn:
        if not chat_input.strip():
            st.error("Input kosong. Silakan paste data dokumen terlebih dahulu.")
        else:
            processing_container = st.empty()
            start_time = time.time()
            
            with processing_container.container():
                st.markdown("""<div class='processing-box'><div class='processing-title'>Mengekstraksi data dengan indoBERT...</div>""", unsafe_allow_html=True)
                st.progress(0.45)
                st.markdown("</div>", unsafe_allow_html=True)
            
            db_should_parse = True
            db_raw_chat_id = None
            if DB_PERSISTENCE_ENABLED and db_prepare_chat_for_parsing is not None:
                try:
                    db_should_parse, db_raw_chat_id = db_prepare_chat_for_parsing(chat_input)
                except Exception:
                    db_should_parse = True
                    db_raw_chat_id = None

            if not db_should_parse:
                processing_container.empty()
                df_saved = load_df_office_from_db()
                if df_saved is not None and not df_saved.empty:
                    st.session_state['df_office'] = df_saved
                    st.session_state.waktu = "0.0s"
                    st.session_state.baris = f"{len(df_saved)} Order"
                    st.session_state.processing_time = 0.0
                st.info("Chat ini sudah pernah diupload. Data lama dipertahankan (tidak diproses ulang).")
                st.rerun()

            formatted_input = auto_format_chat_input(chat_input)
            temp_path = "temp.txt"
            with open(temp_path, "w", encoding="utf-8") as f: 
                f.write(formatted_input)
            
            df_raw = get_processor(
                model_path_override=APP_MODEL_PATH,
                event_model_path_override=APP_EVENT_MODEL_PATH,
                event_threshold=APP_EVENT_THRESHOLD,
            ).process_file(temp_path)

            if df_raw is not None and not df_raw.empty:
                df_proc = preprocess_context(df_raw)
                df_before_revision = enforce_block_quota(df_proc)
                
                # Terapkan fungsi revisi yang sudah DIPERBAIKI
                df_after_revision = apply_revisions_from_chat(chat_input, df_before_revision.copy())
                df_final = df_after_revision.copy()
                df_final = apply_driver_pair_from_text(df_final)
                df_final = apply_phone_pair_from_text(df_final)
                if 'PLATE' in df_final.columns:
                    df_final['PLATE'] = df_final['PLATE'].apply(clean_plate_value)
                
                df_office = pd.DataFrame()
                df_office['No.'] = range(1, len(df_final) + 1)

                job_start = st.session_state.get('job_start', 1)
                job_company = st.session_state.get('job_company', 'JNE').upper()
                job_month = st.session_state.get('job_month', 'II')
                job_year = st.session_state.get('job_year', 2026)
                effective_start = job_start

                df_office['Job Number'] = [f"{effective_start+i:03d}/{job_company}-RAFAY/{job_month}/{job_year}" for i in range(len(df_final))]
                ro_col = None
                muat_col = None
                if 'RO_DATE' in df_final.columns and df_final['RO_DATE'].astype(str).str.strip().any():
                    ro_col = 'RO_DATE'
                elif 'DATE' in df_final.columns and df_final['DATE'].astype(str).str.strip().any():
                    ro_col = 'DATE'

                if 'DATE' in df_final.columns and df_final['DATE'].astype(str).str.strip().any():
                    muat_col = 'DATE'
                elif 'LOAD_DATE' in df_final.columns and df_final['LOAD_DATE'].astype(str).str.strip().any():
                    muat_col = 'LOAD_DATE'
                elif ro_col:
                    muat_col = ro_col

                df_office['Tgl RO'] = df_final[ro_col].apply(format_date_custom) if ro_col else ""
                df_office['Tgl Muat'] = df_final[muat_col].apply(format_date_custom) if muat_col else ""
                df_office['Pickup'] = df_final['ORIGIN'].apply(normalize_origin)
                df_office['Tujuan'] = df_final['DESTINATION'].apply(clean_destination_format)
                df_office['No. Plat'] = df_final['PLATE'].str.upper()
                df_office['Type Truck'] = df_final['UNIT_TYPE'].str.upper()
                df_office['Driver'] = df_final['DRIVER'].fillna("").astype(str).str.title()
                df_office['Kontak Driver'] = df_final['PHONE']
                def _is_filled(val):
                    if val is None:
                        return False
                    s = str(val).strip()
                    if not s:
                        return False
                    if s.lower() in ["-", "null", "none", "nan", "undefined"]:
                        return False
                    return True
                def _classify_status(row):
                    fields = [
                        'Job Number', 'Tgl RO', 'Tgl Muat', 'Pickup', 'Tujuan',
                        'No. Plat', 'Type Truck', 'Driver', 'Kontak Driver'
                    ]
                    filled = sum(1 for f in fields if _is_filled(row.get(f)))
                    if filled == 9:
                        return "ASSIGNED"
                    if filled >= 3:
                        return "PARTIAL"
                    return "UNASSIGNED"
                df_office['status_unit'] = df_office.apply(_classify_status, axis=1)

                # Sorting output berdasarkan Tgl RO lalu Tgl Muat
                df_office['_sort_muat'] = df_office['Tgl Muat'].apply(parse_date_custom)
                df_office['_sort_ro'] = df_office['Tgl RO'].apply(parse_date_custom)
                df_office = df_office.sort_values(
                    by=['_sort_ro', '_sort_muat', 'No.'],
                    na_position='last'
                ).reset_index(drop=True)
                df_office = df_office.drop(columns=['_sort_muat', '_sort_ro'])
                # Renumber setelah sorting
                df_office['No.'] = range(1, len(df_office) + 1)
                df_office['Job Number'] = [f"{effective_start+i:03d}/{job_company}-RAFAY/{job_month}/{job_year}" for i in range(len(df_office))]

                if DB_PERSISTENCE_ENABLED and db_save_parsed_rows is not None and db_raw_chat_id:
                    try:
                        db_rows = office_df_to_parser_rows(df_office)
                        db_save_parsed_rows(db_raw_chat_id, db_rows)
                        df_saved = load_df_office_from_db()
                        if df_saved is not None and not df_saved.empty:
                            df_office = df_saved
                    except Exception as e:
                        # Jangan ganggu alur parser jika penyimpanan DB gagal.
                        st.warning(f"Penyimpanan ke DB gagal: {e}")

                end_time = time.time()
                processing_time = round(end_time - start_time, 2)

                processing_container.empty()
                st.session_state['df_office'] = df_office
                st.session_state.waktu = f"{processing_time}s"
                st.session_state.baris = f"{len(df_office)} Order"
                st.session_state.processing_time = processing_time

                st.rerun()
            else:
                processing_container.empty()
                st.error("Ekstraksi data gagal. Silakan periksa format input dokumen.")
                
            if os.path.exists(temp_path): os.remove(temp_path)
                
    if 'df_office' in st.session_state:
        st.divider()
        st.markdown("<div class='result-container'>", unsafe_allow_html=True)
        st.markdown("<div class='result-header'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='3' y1='9' x2='21' y2='9'></line><line x1='9' y1='21' x2='9' y2='9'></line></svg>Hasil Ekstraksi</div>", unsafe_allow_html=True)
        filter_col, mode_col, assigned_col, partial_col = st.columns([1, 1, 1, 1], gap="large")
        with filter_col:
            filter_label = st.selectbox(
                "Filter Status",
                ["All", "Assigned", "Partial"],
                index=0
            )
        with mode_col:
            job_number_mode = st.selectbox(
                "Mode Nomor Job",
                ["Ringkas per Status", "Ikuti Urutan Master"],
                index=0,
                help="Ringkas per Status: nomor berurutan rapi di filter Assigned/Partial. Ikuti Urutan Master: nomor mengikuti urutan data All."
            )

        def _apply_status_filter(df_in, label):
            if label == "Assigned":
                return df_in[df_in['status_unit'].str.upper() == "ASSIGNED"]
            if label == "Partial":
                return df_in[df_in['status_unit'].str.upper() == "PARTIAL"]
            if label == "Unassigned":
                return df_in[df_in['status_unit'].str.upper() == "UNASSIGNED"]
            return df_in

        def _parse_job_number_local(value):
            if value is None:
                return None
            s = str(value).strip()
            m = re.match(r"^(\d+)\s*/\s*([A-Za-z0-9]+)-RAFAY\s*/\s*([IVX]+)\s*/\s*(\d{4})$", s)
            if not m:
                return None
            return int(m.group(1)), m.group(2).upper(), m.group(3).upper(), int(m.group(4))

        def _get_job_base(df_source):
            if df_source is not None and not df_source.empty and 'Job Number' in df_source.columns:
                for v in df_source['Job Number']:
                    parsed = _parse_job_number_local(v)
                    if parsed:
                        return parsed
            # Fallback ke konfigurasi UI saat parse tidak tersedia
            return (
                int(st.session_state.get('job_start', 1)),
                str(st.session_state.get('job_company', 'JNE')).upper(),
                str(st.session_state.get('job_month', 'II')).upper(),
                int(st.session_state.get('job_year', 2026)),
            )

        def _with_adaptive_job_number(df_in, job_base, enabled=True):
            out = df_in.copy()
            if out.empty:
                return out
            if enabled and 'No.' in out.columns:
                out['No.'] = range(1, len(out) + 1)
            if enabled and 'Job Number' in out.columns and job_base:
                seq_start, comp, mon, yr = job_base
                out['Job Number'] = [f"{seq_start+i:03d}/{comp}-RAFAY/{mon}/{yr}" for i in range(len(out))]
            return out

        df_all = st.session_state['df_office']
        if 'Vendor' in df_all.columns:
            df_all = df_all.drop(columns=['Vendor'])
            st.session_state['df_office'] = df_all
        assigned_count = int((df_all['status_unit'].str.upper() == "ASSIGNED").sum()) if 'status_unit' in df_all.columns else 0
        partial_count = int((df_all['status_unit'].str.upper() == "PARTIAL").sum()) if 'status_unit' in df_all.columns else 0
        with assigned_col:
            st.markdown(
                (
                    "<div class='stat-control'>"
                    "<div class='stat-control-label'>Assigned</div>"
                    f"<div class='stat-chip'><span class='stat-chip-label'>Assigned</span><span class='stat-chip-value'>{assigned_count}</span></div>"
                    "</div>"
                ),
                unsafe_allow_html=True
            )
        with partial_col:
            st.markdown(
                (
                    "<div class='stat-control'>"
                    "<div class='stat-control-label'>Partial</div>"
                    f"<div class='stat-chip'><span class='stat-chip-label'>Partial</span><span class='stat-chip-value'>{partial_count}</span></div>"
                    "</div>"
                ),
                unsafe_allow_html=True
            )

        job_base = _get_job_base(df_all)
        adaptive_enabled = (job_number_mode == "Ringkas per Status")
        df_all_view = _with_adaptive_job_number(df_all, job_base, enabled=adaptive_enabled)
        df_assigned_view = _with_adaptive_job_number(_apply_status_filter(df_all, "Assigned"), job_base, enabled=adaptive_enabled)
        df_partial_view = _with_adaptive_job_number(_apply_status_filter(df_all, "Partial"), job_base, enabled=adaptive_enabled)

        if filter_label == "All":
            df_view = df_all_view
        elif filter_label == "Assigned":
            df_view = df_assigned_view
        else:
            df_view = df_partial_view

        dl_col1, dl_col2, _ = st.columns([1, 1, 2], gap="small")
        def _to_excel_bytes(df_in):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_in.to_excel(writer, index=False, sheet_name='Orders')
                wb = writer.book
                ws = writer.sheets['Orders']
                h_fmt = wb.add_format({'bold': True, 'bg_color': '#efefef', 'font_color': 'black', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                b_fmt = wb.add_format({'border': 1, 'valign': 'vcenter'})
                for c, val in enumerate(df_in.columns): ws.write(0, c, val, h_fmt)
                ws.set_column('A:A', 5)
                ws.set_column('B:M', 18)
                for r in range(len(df_in)):
                    for c in range(len(df_in.columns)):
                        val = df_in.iloc[r, c]
                        ws.write(r+1, c, "" if pd.isna(val) else val, b_fmt)
            return buffer.getvalue()

       

        def _status_row_style(row):
            status = str(row.get('status_unit', '')).strip().upper()
            if status == "ASSIGNED":
                return ['background-color: rgba(34, 197, 94, 0.14); color: #000000;'] * len(row)
            if status == "PARTIAL":
                return ['background-color: rgba(250, 204, 21, 0.22); color: #000000;'] * len(row)
            if status == "UNASSIGNED":
                return ['background-color: rgba(0, 0, 0, 0.07); color: #000000;'] * len(row)
            return [''] * len(row)
        st.dataframe(
            df_view.style.apply(_status_row_style, axis=1),
            use_container_width=True,
            height=min(1600, max(560, 44 + (len(df_view) * 35)))
        )

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
