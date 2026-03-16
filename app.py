import streamlit as st
import pandas as pd
from io import BytesIO
import os
import sys
import re
import sqlite3
from pathlib import Path
from datetime import datetime
import time

# Setup Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.inference.batch_processor import ChatBatchProcessor

# --- KONFIGURASI RAFAY IDP v2.0 ---
DRIVER_BLACKLIST = ["RAFAY","AKBAR","ADMIN","JNE","LOGISTIK","EXPEDISI","PENGIRIM","ONCALL","REQUEST"]

# --- 0. HELPER FUNCTIONS ---
def extract_time_format(time_str):
    time_str = str(time_str).strip().upper()
    if "SEGERA" in time_str:
        return ("SEGERA", "segera")
    m = re.search(r'(\d{1,2})[:\.](\d{2})', time_str)
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

    for line in lines:
        header_timestamp_pattern = r'\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
        timestamp_match = re.search(header_timestamp_pattern, line)
        if timestamp_match:
            # Timestamp WhatsApp hanya metadata waktu chat, tidak boleh menjadi Tgl Muat.
            # Reset konteks tanggal per pesan baru agar tidak carry-over ke pesan berikutnya.
            current_global_date = ""
            current_block_date = ""
            # Netralisasi tanggal timestamp agar model tidak mengekstraknya sebagai DATE.
            # Tetap pertahankan bracket token supaya pemecahan chunk tetap stabil.
            line = re.sub(header_timestamp_pattern, "[WA_TS]", line)

        is_request_header = re.search(r"(?i)(?:REQUEST|ONCALL|TAMBAHAN)", line)
        if is_request_header:
            header_match = re.search(date_header_pattern, line, re.IGNORECASE)
            if header_match:
                current_global_date = header_match.group(1)
                current_block_date = current_global_date
            else:
                # Header tanpa tanggal: pastikan Tgl Muat tidak terisi dari konteks sebelumnya.
                current_global_date = ""
                current_block_date = ""
            formatted_lines.append(line)
            continue

        time_date_slash_line = re.search(
            r'(?i)Waktu\s*loading\s*:\s*\d{1,2}[:.]\d{2}\s*[\\/]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})',
            line
        )
        match = None if time_date_slash_line else re.search(pattern_with_date, line)
        if match:
            prefix = match.group(1)
            jam = match.group(2).strip()
            tgl = match.group(3).strip()
            jam_clean, _ = extract_time_format(jam)
            formatted_lines.append(f"\nREQUEST ORDER KHUSUS {tgl}")
            formatted_lines.append(f"{prefix}{jam_clean}")
            current_global_date = tgl
            current_block_date = tgl
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
            else:
                date_in_value = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', jam_raw)
                if not date_in_value:
                    date_in_value = re.search(r'(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4})', jam_raw)
                if date_in_value:
                    jam_part = jam_raw[:date_in_value.start()].strip()
                    jam_part = re.sub(r'[\\/\\-]+\\s*$', '', jam_part).strip()
                    tgl_part = date_in_value.group(1)
                    jam_clean, _ = extract_time_format(jam_part)
                    formatted_lines.append(f"Waktu loading : {jam_clean} {tgl_part}")
                    current_global_date = tgl_part
                    current_block_date = tgl_part
                else:
                    jam_clean, _ = extract_time_format(jam_raw)
                    if current_global_date:
                        formatted_lines.append(f"Waktu loading : {jam_clean} {current_global_date}")
                    else:
                        formatted_lines.append(f"Waktu loading : {jam_clean}")
            continue

        formatted_lines.append(line)

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
    text = str(original_text)
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
    m = re.search(r'(?im)^\s*Rute\s*(?:/|\s+)\s*(?:tujuan|tuj(?:u(?:an)?)?)\s*:\s*([^\n\r]+)', str(text))
    return m.group(1).strip() if m else ""

def extract_origin_from_text(text):
    if pd.isna(text) or not str(text).strip():
        return ""
    m = re.search(r'(?im)^\s*Lokasi\s*:\s*([^\n\r]+)', str(text))
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
                m_next = re.search(date_pattern, lines[idx + look_ahead])
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
    candidates = []
    date_token = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[a-zA-Z]{3,}\s+\d{2,4}'
    date_pattern = rf'\b({date_token})\b'
    khusus_pattern = rf'(?i)REQUEST\s+ORDER\s+KHUSUS\s+({date_token})'
    for match in re.finditer(r'(?im)^\s*Waktu\s*loading\s*:\s*([^\n\r]+)', str(text)):
        val = str(match.group(1)).strip()
        if not val:
            continue
        pos = match.start()
        val_upper = val.upper()
        has_segera = "SEGERA" in val_upper
        date_part = ""
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
                if re.search(r'(?i)\b(Lokasi|Rute|Waktu\s*loading)\b', orig_text):
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
            if not str(row.get('PLATE', '')) or str(row.get('PLATE', '')).lower() == 'nan':
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
            target_qty += extra_unit_count

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
        elif block_text:
            loading_candidates_list = extract_loading_candidates(block_text)
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
                if not str(candidate.get('DRIVER', '')).strip() and block_driver_pair:
                    candidate['DRIVER'] = block_driver_pair
                if not str(candidate.get('PLATE', '')).strip() and block_plate:
                    candidate['PLATE'] = block_plate
                if not str(candidate.get('PHONE', '')).strip() and block_phone_pair:
                    candidate['PHONE'] = block_phone_pair
                final_rows.append(candidate)
            else:
                clean_slot = header_row.copy()
                clean_slot['DRIVER'] = ""; clean_slot['PLATE'] = ""; clean_slot['PHONE'] = ""; clean_slot['TIME'] = ""; clean_slot['UNIT_QTY'] = 1
                header_date = _clean_empty(header_row.get('DATE'))
                if header_date and re.search(r'\d', str(header_date)): clean_slot['DATE'] = header_date
                else: clean_slot['DATE'] = ""
                if block_ro_date:
                    clean_slot['RO_DATE'] = block_ro_date
                if block_muat_date:
                    clean_slot['DATE'] = block_muat_date
                elif block_has_segera and block_ro_date:
                    clean_slot['DATE'] = block_ro_date
                final_rows.append(clean_slot)
    return pd.DataFrame(final_rows).reset_index(drop=True)

# --- [FITUR BARU] REVISI PINTAR BERBASIS MEMORI ---
def apply_revisions_from_chat(chat_text, df_final):
    """
    Menangkap pesan revisi langsung dari teks asli chat WhatsApp dan
    menerapkannya ke order eksisting tanpa membuat baris baru.
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
        payload = {
            'target_time': None,
            'target_origin': "",
            'target_route': "",
            'target_unit': "",
            'updates': {}
        }

        # Context target: waktu loading / jam
        time_match = re.search(r'(?i)(?:jam|pukul|waktu(?:\s+loading)?)\s*:?\s*(\d{1,2}(?:[:.]\d{2})?)', msg_text)
        if time_match:
            payload['target_time'] = normalize_time(time_match.group(1))

        # Context target: lokasi
        lokasi_match = re.search(r'(?im)^\s*Lokasi\s*:\s*([^\n\r]+)', msg_text)
        if lokasi_match:
            payload['target_origin'] = normalize_token(lokasi_match.group(1))

        # Context target: rute
        route_match = re.search(r'(?im)^\s*Rute(?:\s*/\s*|\s+)tujuan\s*:\s*([^\n\r]+)', msg_text)
        if route_match:
            payload['target_route'] = normalize_route(route_match.group(1))

        # Context target: unit type (optional)
        unit_match = re.search(r'(?im)^\s*(?:jenis\s+unit|type\s+truck)\s*:\s*([^\n\r]+)', msg_text)
        if unit_match:
            payload['target_unit'] = normalize_unit_type(unit_match.group(1))
        else:
            unit_inline = re.search(r'(?i)\bunit\s+([a-zA-Z][a-zA-Z0-9\s]{1,20})', msg_text)
            if unit_inline:
                unit_candidate = unit_inline.group(1).strip()
                if not re.match(r'(?i)^(?:jam|pukul|waktu)\b', unit_candidate):
                    payload['target_unit'] = normalize_unit_type(unit_candidate)

        # Revised fields: driver / nopol / phone
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
        return max(best)  # paling recent

    def find_best_match(payload):
        candidate_indices = [idx for idx in df.index if not bool(revision_mask.loc[idx])]
        if not candidate_indices:
            return None

        # Priority a) waktu_loading
        if payload['target_time']:
            by_time = [idx for idx in candidate_indices if row_time(idx) == payload['target_time']]
            if by_time:
                return pick_best(by_time, payload)

        # Priority b) lokasi
        if payload['target_origin']:
            by_origin = [idx for idx in candidate_indices if row_origin(idx) == payload['target_origin']]
            if by_origin:
                return pick_best(by_origin, payload)

        # Priority c) rute
        if payload['target_route']:
            by_route = [idx for idx in candidate_indices if row_route(idx) == payload['target_route']]
            if by_route:
                return pick_best(by_route, payload)

        # Priority d) order paling recent sebelum revisi
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

def calculate_extraction_accuracy(df_raw, df_final):
    if df_final is None or df_final.empty:
        return 0.0
    critical_fields = ['DRIVER', 'PLATE', 'DATE', 'TIME', 'ORIGIN', 'DESTINATION', 'UNIT_TYPE']
    total_fields = len(critical_fields) * len(df_final)
    filled_fields = 0
    for field in critical_fields:
        if field in df_final.columns:
            filled_fields += df_final[field].notna().sum()
    accuracy = round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0.0
    return min(accuracy, 100.0)

# =================================================================================
# --- FRONTEND UI: WHITE THEME - PROFESSIONAL EDITION ---
# =================================================================================

st.set_page_config(page_title="Rafay Logistics IDP v2.0", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-color: #0f1116;
            --bg-elev-1: #161b22;
            --bg-elev-2: #1d2430;
            --card-bg: #121821;
            --border-color: #2a3441;
            --accent-color: #007acc;
            --accent-strong: #1da1ff;
            --text-main: #e6edf3;
            --text-muted: #9fb1c3;
            --text-dim: #7f8da3;
            --success-color: #2ea043;
            --warning-color: #d29922;
        }
        
        .stApp {
            background: radial-gradient(1200px 400px at 12% -10%, rgba(0, 122, 204, 0.18), transparent 60%),
                        linear-gradient(180deg, #0f1116 0%, #0b0f14 100%) !important;
            font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: var(--text-main) !important;
        }

        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
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
            box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
        }
        .status-dot { width: 8px; height: 8px; background-color: var(--success-color); border-radius: 50%; box-shadow: 0 0 8px rgba(46, 160, 67, 0.6); }

        .input-panel {
            background-color: var(--bg-elev-1); border: 1px solid var(--border-color);
            border-radius: 10px; padding: 18px; height: 100%;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }
        .input-panel-wide { padding: 16px 18px 12px 18px; }
        .panel-header { display: flex; align-items: center; gap: 10px; font-weight: 700; color: var(--text-main); margin-bottom: 12px; }
        .badge-ml { background-color: rgba(0, 122, 204, 0.12); color: var(--accent-strong); font-size: 0.65rem; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(0, 122, 204, 0.35); font-weight: 600; }
        
        .tab-mockup { display: flex; gap: 8px; margin-bottom: 12px; }
        .tab-btn { background-color: var(--bg-elev-2); border: 1px solid var(--border-color); color: var(--text-main); padding: 8px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; width: 50%; text-align: center; cursor: default; }
        .tab-inactive { background-color: transparent; color: var(--text-dim); border-style: dashed; }
        
        .stTextArea textarea {
            background-color: #0c121a !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important;
            border-radius: 8px !important; font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace !important;
            font-size: 0.82rem; padding: 14px; line-height: 1.5;
        }
        .stTextArea textarea:focus { border-color: var(--accent-color) !important; box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.25) !important;}
        
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input {
            background-color: #0c121a !important; color: var(--text-main) !important; border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #007acc 0%, #1da1ff 100%) !important; color: #0b1117 !important; border: none !important;
            border-radius: 8px !important; padding: 11px 16px !important; font-weight: 700 !important; width: 100% !important; margin-top: 12px; transition: 0.2s;
            box-shadow: 0 6px 18px rgba(0, 122, 204, 0.35);
        }
        div.stButton > button:hover { filter: brightness(1.08); transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0, 122, 204, 0.4); }

        .output-panel {
            background-color: var(--bg-elev-1); border: 1px solid var(--border-color);
            border-radius: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 500px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }
        .out-icon { background-color: rgba(0, 122, 204, 0.08); padding: 18px; border-radius: 14px; margin-bottom: 18px; position: relative; }
        .out-icon svg { width: 38px; color: var(--accent-color); }
        .out-badge { position: absolute; bottom: -6px; right: -6px; background: var(--accent-color); color: #0b1117; font-size: 0.6rem; font-weight: 700; padding: 4px 8px; border-radius: 999px; }
        .out-title { color: var(--text-main); font-weight: 700; font-size: 1.15rem; margin-bottom: 8px; }
        .out-desc { color: var(--text-muted); font-size: 0.82rem; text-align: center; max-width: 420px; line-height: 1.6; margin-bottom: 24px; }
        
        .out-options { display: flex; gap: 12px; }
        .opt-box { background: var(--card-bg); border: 1px solid var(--border-color); padding: 10px 16px; border-radius: 8px; text-align: center; }
        .opt-box p { margin: 0; color: var(--text-main); font-weight: 600; font-size: 0.82rem; }
        .opt-box span { color: var(--text-dim); font-size: 0.7rem; display: block; margin-top: 2px; }

        [data-testid="stDataFrame"] { background-color: var(--bg-elev-1) !important; }
        .stDataFrame { background-color: var(--bg-elev-1) !important; }
        [data-testid="stDataFrame"] > div { background-color: var(--bg-elev-1) !important; }
        [data-testid="stDataFrame"] tbody td { color: var(--text-main) !important; background-color: #0f151d !important; border-color: var(--border-color) !important; }
        [data-testid="stDataFrame"] thead th { background-color: #19212b !important; color: var(--text-main) !important; border-color: var(--border-color) !important; font-weight: 600; }
        [data-testid="stDataFrame"] tbody tr:nth-child(odd) { background-color: #0f151d !important; }
        [data-testid="stDataFrame"] tbody tr:nth-child(even) { background-color: #111924 !important; }
        [data-testid="stDataFrame"] table { border-color: var(--border-color) !important; border-collapse: collapse; }
        [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td { border-color: var(--border-color) !important; padding: 10px 12px; }
        [data-testid="stDataFrame"] tbody tr:hover { background-color: rgba(0, 122, 204, 0.18) !important; }
        
        div.stDownloadButton > button { background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%) !important; color: #0b1117 !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; width: 100% !important; margin-top: 12px; box-shadow: 0 6px 18px rgba(46, 160, 67, 0.35); }
        div.stDownloadButton > button:hover { filter: brightness(1.05); box-shadow: 0 10px 24px rgba(46, 160, 67, 0.4); }

        .result-container { background-color: var(--bg-elev-1); padding: 22px; border-radius: 10px; border: 1px solid var(--border-color); box-shadow: 0 8px 24px rgba(0,0,0,0.35); }
        .result-header { color: var(--text-main); font-weight: 700; font-size: 1rem; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }

        .dashboard-container { width: 100%; margin-bottom: 16px; }
        .metric-box { background-color: var(--bg-elev-2); border: 1px solid var(--border-color); border-radius: 10px; padding: 18px; text-align: center; box-shadow: 0 6px 18px rgba(0,0,0,0.25); }
        .metric-box-label { font-size: 0.7rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
        .metric-box-value { font-size: 1.6rem; font-weight: 700; color: var(--accent-strong); line-height: 1.2; }

        .muted-preview { font-size: 0.86rem; color: var(--text-muted); }
        .processing-box { background-color: var(--bg-elev-1); border: 1px solid var(--border-color); border-radius: 10px; padding: 22px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); }
        .processing-title { font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 12px; }
        .section-spacer { height: 14px; }
        .full-width { width: 100%; }

        .stMarkdown p, .stMarkdown li, .stMarkdown span { color: var(--text-main); }
        .stMarkdown small, .stMarkdown .caption { color: var(--text-muted); }
        code, pre { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace !important; }
        .stAlert, .stInfo, .stWarning, .stSuccess { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_processor(): return ChatBatchProcessor()

def init_db():
    conn = sqlite3.connect("rafay_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_number TEXT UNIQUE,
            tgl_ro TEXT,
            tgl_muat TEXT,
            vendor TEXT,
            pickup TEXT,
            tujuan TEXT,
            nopol TEXT,
            type_truck TEXT,
            driver TEXT,
            kontak_driver TEXT,
            jam_loading TEXT,
            status TEXT DEFAULT 'Valid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def render_top_ui(proses_waktu="--", baris="--", akurasi="--"):
    st.markdown(f"""
        <div class="top-navbar">
            <div class="nav-logo">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-color)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 1 0 0-20z"></path><path d="M12 6v6l4 2"></path></svg>
                <div>
                    <h1 class="nav-title">Rafay Logistics <span class="nav-accent">IDP</span></h1>
                    <p class="nav-subtitle">Intelligent Document Processing v1.0 (LayoutLMv3)</p>
                </div>
            </div>
            <div class="nav-status">
                <div class="status-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 20 9 4 6 12 2 12"></polyline></svg>
                    Model Engine <span class="status-dot"></span> Ready
                </div>
                <div class="status-badge">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    {datetime.now().strftime("%H:%M:%S")}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def main():
    init_db()
    if 'waktu' not in st.session_state: st.session_state.waktu = "--"
    if 'baris' not in st.session_state: st.session_state.baris = "--"
    if 'akurasi' not in st.session_state: st.session_state.akurasi = "--"
    if 'processing_time' not in st.session_state: st.session_state.processing_time = 0.0
    
    render_top_ui(st.session_state.waktu, st.session_state.baris, st.session_state.akurasi)
    
    st.markdown("""
    <div class="input-panel input-panel-wide">
        <div class="panel-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            Input Dokumen <span class="badge-ml">VISION + NLP</span>
        </div>
        <div class="tab-mockup">
            <div class="tab-btn">WhatsApp Chat</div>
            <div class="tab-btn tab-inactive">Dokumen PDF</div>
        </div>
    </div>
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

    preview_format = f"{job_start:03d}/{job_company.upper()}-RAFAY/{job_month}/{job_year}"
    st.markdown(f"<span class='muted-preview'>Preview: <code>{preview_format}</code></span>", unsafe_allow_html=True)

    chat_input = st.text_area(
        "Input", height=260, label_visibility="collapsed",
        placeholder="Paste data chat WhatsApp atau dokumen logistik di sini..."
    )

    btn = st.button("Mulai Ekstraksi Data")

    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)

    if not btn and 'df_office' not in st.session_state:
        st.markdown("""
        <div class="output-panel full-width">
            <div class="out-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                <div class="out-badge">AI</div>
            </div>
            <div class="out-title">Siap Memproses Data</div>
            <div class="out-desc">Input dokumen logistik Rafay pada panel input, lalu klik Mulai Ekstraksi.</div>
        </div>
        """, unsafe_allow_html=True)
        
    if btn:
        if not chat_input.strip():
            st.error("Input kosong. Silakan paste data dokumen terlebih dahulu.")
        else:
            processing_container = st.empty()
            start_time = time.time()
            
            with processing_container.container():
                st.markdown("""<div class='processing-box'><div class='processing-title'>Mengekstraksi data dengan AI...</div>""", unsafe_allow_html=True)
                st.progress(0.45)
                st.markdown("</div>", unsafe_allow_html=True)
            
            formatted_input = auto_format_chat_input(chat_input)
            temp_path = "temp.txt"
            with open(temp_path, "w", encoding="utf-8") as f: 
                f.write(formatted_input)
            
            df_raw = get_processor().process_file(temp_path)

            if df_raw is not None and not df_raw.empty:
                df_proc = preprocess_context(df_raw)
                df_final = enforce_block_quota(df_proc)
                
                # Terapkan fungsi revisi yang sudah DIPERBAIKI
                df_final = apply_revisions_from_chat(chat_input, df_final)
                df_final = apply_driver_pair_from_text(df_final)
                df_final = apply_phone_pair_from_text(df_final)
                if 'PLATE' in df_final.columns:
                    df_final['PLATE'] = df_final['PLATE'].apply(clean_plate_value)

                accuracy = calculate_extraction_accuracy(df_raw, df_final)
                
                df_office = pd.DataFrame()
                df_office['No.'] = range(1, len(df_final) + 1)

                job_start = st.session_state.get('job_start', 1)
                job_company = st.session_state.get('job_company', 'JNE').upper()
                job_month = st.session_state.get('job_month', 'II')
                job_year = st.session_state.get('job_year', 2026)

                df_office['Job Number'] = [f"{job_start+i:03d}/{job_company}-RAFAY/{job_month}/{job_year}" for i in range(len(df_final))]
                df_office['Tgl RO'] = df_final['RO_DATE'].apply(format_date_custom) if 'RO_DATE' in df_final.columns else ""
                df_office['Tgl Muat'] = df_final['DATE'].apply(format_date_custom)
                df_office['Vendor'] = ""
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

                # Sorting output berdasarkan Tgl Muat lalu Tgl RO
                df_office['_sort_muat'] = df_office['Tgl Muat'].apply(parse_date_custom)
                df_office['_sort_ro'] = df_office['Tgl RO'].apply(parse_date_custom)
                df_office = df_office.sort_values(
                    by=['_sort_muat', '_sort_ro', 'No.'],
                    na_position='last'
                ).reset_index(drop=True)
                df_office = df_office.drop(columns=['_sort_muat', '_sort_ro'])
                # Renumber setelah sorting
                df_office['No.'] = range(1, len(df_office) + 1)
                df_office['Job Number'] = [f"{job_start+i:03d}/{job_company}-RAFAY/{job_month}/{job_year}" for i in range(len(df_office))]

                end_time = time.time()
                processing_time = round(end_time - start_time, 2)

                processing_container.empty()
                st.session_state['df_office'] = df_office
                st.session_state.waktu = f"{processing_time}s"
                st.session_state.baris = f"{len(df_office)} Order"
                st.session_state.akurasi = f"{accuracy}%"
                st.session_state.processing_time = processing_time

                st.rerun()
            else:
                processing_container.empty()
                st.error("Ekstraksi data gagal. Silakan periksa format input dokumen.")
                
            if os.path.exists(temp_path): os.remove(temp_path)
                
    if 'df_office' in st.session_state:
        dashboard_col1, dashboard_col2 = st.columns(2, gap="medium")
        with dashboard_col1:
            st.markdown(f"""<div class="metric-box"><div class="metric-box-label">Processing Time</div><div class="metric-box-value">{st.session_state.get('processing_time', 0.0)}s</div></div>""", unsafe_allow_html=True)
        with dashboard_col2:
            st.markdown(f"""<div class="metric-box"><div class="metric-box-label">Total Records</div><div class="metric-box-value">{len(st.session_state['df_office'])}</div></div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("<div class='result-container'>", unsafe_allow_html=True)
        st.markdown("<div class='result-header'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='3' y1='9' x2='21' y2='9'></line><line x1='9' y1='21' x2='9' y2='9'></line></svg>Hasil Ekstraksi</div>", unsafe_allow_html=True)
        filter_col, _ = st.columns([1, 3], gap="large")
        with filter_col:
            filter_label = st.selectbox(
                "Filter Status",
                ["All", "Assigned", "Partial", "Unassigned"],
                index=0
            )

        def _apply_status_filter(df_in, label):
            if label == "Assigned":
                return df_in[df_in['status_unit'].str.upper() == "ASSIGNED"]
            if label == "Partial":
                return df_in[df_in['status_unit'].str.upper() == "PARTIAL"]
            if label == "Unassigned":
                return df_in[df_in['status_unit'].str.upper() == "UNASSIGNED"]
            return df_in

        df_all = st.session_state['df_office']
        df_view = _apply_status_filter(df_all, filter_label)

        dl_col1, dl_col2, _ = st.columns([1, 1, 2], gap="small")
        def _to_excel_bytes(df_in):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_in.to_excel(writer, index=False, sheet_name='Orders')
                wb = writer.book
                ws = writer.sheets['Orders']
                h_fmt = wb.add_format({'bold': True, 'bg_color': '#0F766E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                b_fmt = wb.add_format({'border': 1, 'valign': 'vcenter'})
                for c, val in enumerate(df_in.columns): ws.write(0, c, val, h_fmt)
                ws.set_column('A:A', 5)
                ws.set_column('B:M', 18)
                for r in range(len(df_in)):
                    for c in range(len(df_in.columns)):
                        val = df_in.iloc[r, c]
                        ws.write(r+1, c, "" if pd.isna(val) else val, b_fmt)
            return buffer.getvalue()

        with dl_col1:
            st.download_button(
                label="Download All",
                data=_to_excel_bytes(df_all),
                file_name="orders_all.xlsx"
            )
        with dl_col2:
            st.download_button(
                label="Download Assigned",
                data=_to_excel_bytes(_apply_status_filter(df_all, "Assigned")),
                file_name="orders_assigned.xlsx"
            )

        def _status_row_style(row):
            status = str(row.get('status_unit', '')).strip().upper()
            if status == "ASSIGNED":
                return ['background-color: rgba(46, 204, 113, 0.12)'] * len(row)
            if status == "PARTIAL":
                return ['background-color: rgba(241, 196, 15, 0.12)'] * len(row)
            if status == "UNASSIGNED":
                return ['background-color: rgba(231, 76, 60, 0.12)'] * len(row)
            return [''] * len(row)
        st.dataframe(
            df_view.style.apply(_status_row_style, axis=1),
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
