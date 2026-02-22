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

# --- KONFIGURASI RAFAY IDP v2.0 ---
# Template dioptimalkan untuk IndobERT + LayoutLMv3 (Vision + NLP Hybrid)
# White Theme Edition dengan Icon Professional
DRIVER_BLACKLIST = ["RAFAY","AKBAR","ADMIN","JNE","LOGISTIK","EXPEDISI","PENGIRIM","ONCALL","REQUEST"]

# --- 0. HELPER FUNCTIONS ---
def extract_time_format(time_str):
    """
    Extract waktu dari berbagai format (HH:MM, HH.MM, HH, SEGERA, dll)
    Return: (time_str, format_detected)
    """
    time_str = str(time_str).strip().upper()

    # Format SEGERA
    if "SEGERA" in time_str:
        return ("SEGERA", "segera")

    # Format HH:MM atau HH.MM
    m = re.search(r'(\d{1,2})[:\.](\d{2})', time_str)
    if m:
        hour = int(m.group(1))
        minute = m.group(2)
        return (f"{hour:02d}:{minute}", "HH:MM")

    # Format hanya HH
    m = re.search(r'^(\d{1,2})$', time_str.strip())
    if m:
        hour = int(m.group(1))
        return (f"{hour:02d}:00", "HH")

    return (time_str, "unknown")

def auto_format_chat_input(text):
    """
    Format input dari chat WhatsApp/SMS dengan deteksi otomatis struktur waktu & tanggal.
    Kompatibel dengan output IndobERT entity recognition.
    IMPROVED: Menangkap waktu loading standalone di baris terpisah.
    """
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

    # Pattern untuk deteksi Waktu loading dengan tanggal di baris yang sama
    pattern_with_date = r"(?i)(Waktu loading\s*:\s*)(.*?)(\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}|\s+\d{1,2}\s+[a-zA-Z]+\s+\d{4})"
    # Pattern untuk deteksi header dengan tanggal (REQUEST ORDER, ONCALL, TAMBAHAN)
    date_header_pattern = r"(?:REQUEST|ONCALL|TAMBAHAN).*?(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
    # Pattern untuk Waktu loading standalone (format: Waktu loading : <waktu tanpa tanggal>)
    waktu_loading_standalone = r"(?i)Waktu\s+loading\s*:\s*(.+?)(?=\n|$)"

    current_global_date = ""
    current_block_date = ""
    current_header_timestamp = None  # State-based tracking untuk [HH.MM, DD/MM/YYYY]

    for line in lines:
        # FIX: Deteksi header timestamp [HH.MM, DD/MM/YYYY] sebelum REQUEST header
        # Pattern: [HH.MM, DD/MM/YYYY] atau [HH:MM, DD/MM/YYYY] atau [HH:MM, DD-MM-YYYY]
        header_timestamp_pattern = r'\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
        timestamp_match = re.search(header_timestamp_pattern, line)
        if timestamp_match:
            # Extract tanggal dari header dan simpan sebagai state aktif
            current_header_timestamp = timestamp_match.group(2)
            current_global_date = current_header_timestamp
            current_block_date = current_header_timestamp
            formatted_lines.append(line)
            continue

        # Cek apakah ada header REQUEST/ONCALL/TAMBAHAN
        is_request_header = re.search(r"(?i)(?:REQUEST|ONCALL|TAMBAHAN)", line)
        if is_request_header:
            # Cek apakah ada tanggal di header
            header_match = re.search(date_header_pattern, line, re.IGNORECASE)
            if header_match:
                # Header dengan tanggal embedded: update current_global_date
                current_global_date = header_match.group(1)
                current_block_date = current_global_date
            # else: Gunakan state timestamp yang terakhir aktif (dari header [HH.MM, DD/MM/YYYY])
            # Jika tidak ada state timestamp, gunakan current_global_date sebelumnya
            formatted_lines.append(line)
            continue

        # Cek pattern Waktu loading dengan tanggal di baris yang sama
        match = re.search(pattern_with_date, line)
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

        # Cek pattern Waktu loading standalone (tanpa tanggal di baris yang sama)
        standalone_match = re.search(waktu_loading_standalone, line, re.IGNORECASE)
        if standalone_match:
            jam_raw = standalone_match.group(1).strip()
            # Jika waktu ada tanggal di dalam value (e.g., "03:00 05/02/2026")
            # Pattern: waktu diikuti spasi dan tanggal
            date_in_value = re.search(r'(\d{1,2}[./:-]\d{1,2}[./:-]\d{4})', jam_raw)
            if date_in_value:
                jam_part = jam_raw[:date_in_value.start()].strip()
                tgl_part = date_in_value.group(1)
                jam_clean, _ = extract_time_format(jam_part)
                formatted_lines.append(f"Waktu loading : {jam_clean} {tgl_part}")
                current_global_date = tgl_part
                current_block_date = tgl_part
            else:
                # Waktu tanpa tanggal - gunakan current_global_date
                jam_clean, _ = extract_time_format(jam_raw)
                if current_global_date:
                    formatted_lines.append(f"Waktu loading : {jam_clean} {current_global_date}")
                else:
                    formatted_lines.append(f"Waktu loading : {jam_clean}")
            continue

        # Baris biasa tanpa pattern khusus
        formatted_lines.append(line)

    return "\n".join(formatted_lines)

def extract_plate_aggressive(text):
    """
    Ekstraksi plat nomor menggunakan regex dengan support untuk format Indonesia.
    Output dari LayoutLMv3 OCR disambiguasi di sini.
    """
    if pd.isna(text): return ""
    text = str(text).upper()
    match = re.search(r"\b([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})\b", text)
    if match: return match.group(1)
    return ""

def normalize_phone_number(phone):
    """Normalisasi nomor HP: hapus non-digit, handle prefix 62, tanpa spasi."""
    if pd.isna(phone) or not str(phone).strip():
        return ""
    # Hapus semua karakter selain digit
    phone_digits = re.sub(r'\D', '', str(phone))
    if not phone_digits:
        return ""
    # Jika diawali "62", ubah menjadi "0" + sisa angka
    if phone_digits.startswith('62'):
        phone_digits = '0' + phone_digits[2:]
    return phone_digits

def normalize_route(text):
    """Normalisasi format rute: uppercase, pisahkan dengan koma+spasi."""
    if pd.isna(text) or not str(text).strip():
        return ""
    text_str = str(text).strip()
    if text_str.lower() in ['none', 'nan', 'nat']:
        return ""
    
    # Step 1: Uppercase seluruh string
    route = text_str.upper()
    
    # Step 2: Ganti semua "–" dan "/" menjadi "-"
    route = route.replace('–', '-').replace('/', '-')
    
    # Step 3: Hapus spasi berlebih
    route = re.sub(r'\s+', ' ', route)
    
    # Step 4: Split berdasarkan "-" atau "," jika ada
    if '-' in route or ',' in route:
        # Normalize: split by both dash and comma
        # Replace comma dengan dash untuk normalisasi
        route = route.replace(',', '-')
        parts = [p.strip() for p in route.split('-') if p.strip()]
        if len(parts) >= 2:
            return ', '.join(parts)
    
    # Step 5: Jika tidak ada dash/comma, check untuk space separator
    if ' ' in route:
        parts = [p.strip() for p in route.split() if p.strip()]
        if len(parts) > 1:
            return ', '.join(parts)
    
    # Jika tidak ada separator, return as is
    return route.strip()

def clean_driver_name(name):
    """Sanitasi nama driver dengan blacklist penghindaran (admin, logistik, etc)."""
    if not name or pd.isna(name) or str(name).lower() == 'none': return ""
    clean_name = str(name).strip().title()
    for bad_word in DRIVER_BLACKLIST:
        if bad_word.lower() in clean_name.lower(): return ""
    return clean_name

def sanitize_row_data(row):
    """
    Sanitasi data per baris: perbaikan posisi waktu, deteksi SEGERA, validasi format tanggal.
    Tahap post-processing dari IndobERT token classification.
    IMPROVED: Better time format detection dan extraction + FALLBACK REGEX.
    """
    d = str(row.get('DATE', '')).strip()
    t = str(row.get('TIME', '')).strip()
    orig_text = str(row.get('Original_Text', '')).strip()
    drv = str(row.get('DRIVER', '')).strip()

    # Clean invalid values
    if d.lower() in ['none', 'nan', 'nat']: d = ""
    if t.lower() in ['none', 'nan', 'nat']: t = ""

    # Check untuk SEGERA keyword
    has_segera = False
    if "segera" in t.lower(): has_segera = True
    elif "segera" in d.lower(): has_segera = True; d = ""
    elif "segera" in drv.lower(): has_segera = True
    elif "segera" in orig_text.lower(): has_segera = True

    if has_segera:
        t = "SEGERA"
    else:
        # FIX: If DATE contains HH:MM pattern (time), extract and separate them
        # Example: "21:00 04 FEBRUARI 2026" -> DATE="04 FEBRUARI 2026", TIME="21:00"
        time_in_date_pattern = r'^(\d{1,2}:\d{2})\s+(.+)$'
        time_in_date_match = re.search(time_in_date_pattern, d)
        if time_in_date_match:
            potential_time = time_in_date_match.group(1)
            remaining_date = time_in_date_match.group(2)
            if not t or t in ["SEGERA", ""]:
                t = potential_time
            d = remaining_date.strip()

        # Handle waktu yang mungkin ada di DATE field (misplaced time)
        is_time_misplaced = re.match(r'^(\d{1,2}|\d{1,2}[:.]\d{2})$', d)
        if is_time_misplaced:
            if not t or t in ["SEGERA", ""]:
                t = d
            d = ""

        # Standardisasi format waktu
        if t and t != "SEGERA":
            # First, remove extra spaces from time format (03 : 00 -> 03:00)
            t = re.sub(r'\s+', '', t)
            t = t.replace(".", ":").replace("*", "").upper()
            # Format HH:MM
            m = re.search(r'^(\d{1,2}):(\d{2})', t)
            if m:
                hour = int(m.group(1))
                minute = m.group(2)
                t = f"{hour:02d}:{minute}"
            # Format hanya HH
            elif re.match(r'^\d{1,2}$', t):
                hour = int(t.split()[0])  # ambil angka pertama jika ada space
                t = f"{hour:02d}:00"

    # FALLBACK: Jika TIME masih kosong setelah processing, extract dari Original_Text
    if not t or t == "":
        # Cari "Waktu loading : HH:MM" atau "Waktu loading : SEGERA" di Original_Text
        fallback_match = re.search(r"(?i)Waktu\s+loading\s*:\s*([0-9]{1,2}\s*:\s*[0-9]{2}|[0-9]{1,2}|SEGERA)", orig_text)
        if fallback_match:
            waktu_fallback = fallback_match.group(1).strip().upper()
            # Remove extra spaces in time format (03 : 00 -> 03:00)
            waktu_fallback = re.sub(r'\s+', '', waktu_fallback)

            if "SEGERA" in waktu_fallback:
                t = "SEGERA"
            else:
                # Format as HH:MM
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

    # FIX 1: Normalisasi nomor HP
    if 'PHONE' in row:
        raw_phone = str(row.get('PHONE', '')).strip()
        if raw_phone and raw_phone.lower() not in ['none', 'nan', 'nat', '']:
            row['PHONE'] = normalize_phone_number(raw_phone)
        else:
            row['PHONE'] = ""
    
    # FIX 2: Normalisasi format ORIGIN dan DESTINATION
    for route_field in ['ORIGIN', 'DESTINATION']:
        if route_field in row:
            raw_route = str(row.get(route_field, '')).strip()
            if raw_route and raw_route.lower() not in ['none', 'nan', 'nat', '']:
                row[route_field] = normalize_route(raw_route)
            else:
                row[route_field] = ""

    row['DATE'] = d
    row['TIME'] = t
    return row

def repair_headers(df):
    """
    Perbaikan header blok (struktur logistik: qty, origin, destination, unit_type).
    Gunakan forward-fill lookahead untuk menangani incomplete extraction dari LayoutLMv3.
    """
    if df is None or df.empty: return df
    for col in ['DESTINATION', 'ORIGIN', 'UNIT_TYPE']:
        df[col] = df[col].replace(['', 'None', 'NONE', 'nan', 'nan '], pd.NA)
    for i in range(len(df)):
        qty_val = str(df.at[i, 'UNIT_QTY'])
        if any(char.isdigit() for char in qty_val):
            for lookahead in range(1, 4):
                if i + lookahead < len(df):
                    if pd.isna(df.at[i, 'DESTINATION']): df.at[i, 'DESTINATION'] = df.at[i + lookahead, 'DESTINATION']
                    if pd.isna(df.at[i, 'ORIGIN']): df.at[i, 'ORIGIN'] = df.at[i + lookahead, 'ORIGIN']
                    if pd.isna(df.at[i, 'UNIT_TYPE']): df.at[i, 'UNIT_TYPE'] = df.at[i + lookahead, 'UNIT_TYPE']
    return df

def mark_order_block(df):
    """
    Penandaan blok order berdasarkan UNIT_QTY. Setiap kuantitas > 1 adalah header blok baru.
    Hasil dari entity grouping post-IndobERT processing.
    """
    df = df.copy(); df['BLOCK_ID'] = 0; current_block = 0
    for i in range(len(df)):
        qty_raw = str(df.at[i, 'UNIT_QTY'])
        is_header = False
        try:
            q_num = int(''.join(filter(str.isdigit, qty_raw))) if any(char.isdigit() for char in qty_raw) else 0
            if q_num > 1: is_header = True
            elif q_num == 1 and pd.notna(df.at[i, 'UNIT_TYPE']): is_header = True
        except: pass
        if is_header: current_block += 1
        df.at[i, 'BLOCK_ID'] = current_block
    return df

def preprocess_context(df):
    """
    Pipeline preprocessing utama: repair headers → apply revision → mark blocks → forward-fill context per blok.
    Transformasi raw extraction menjadi structured data siap untuk business logic.
    """
    if df is None or df.empty: return df
    df = repair_headers(df)
    df = apply_revision_logic(df)  # Apply revision logic BEFORE marking blocks
    df = mark_order_block(df)
    
    # Proteksi: pastikan semua kolom yang diperlukan ada sebelum groupby + ffill
    required_cols = ['UNIT_TYPE', 'ORIGIN', 'DESTINATION', 'DATE']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    # Forward-fill context per blok
    for col in required_cols:
        df[col] = df.groupby('BLOCK_ID')[col].ffill()
    return df

def enforce_block_quota(df):
    """
    Enforcement quota per blok: jika blok minta 3 unit, pastikan 3 baris dengan driver info.
    Kolom null diisi dari header block atau placeholder kosong jika tidak ada candidate.
    Logika business rule Rafay: 1 blok order = N unit = N drivers.
    """
    if df is None or df.empty: return df
    final_rows = []
    for block_id in df['BLOCK_ID'].unique():
        if block_id == 0: continue
        block_data = df[df['BLOCK_ID'] == block_id].copy()
        target_qty = 1
        for q in block_data['UNIT_QTY']:
            try:
                q_str = ''.join(filter(str.isdigit, str(q)))
                if q_str: target_qty = max(target_qty, int(q_str))
            except: pass
        valid_candidates = []; header_row = None
        for _, row in block_data.iterrows():
            q_val = str(row.get('UNIT_QTY', ''))
            is_master_header = False
            try:
                if int(''.join(filter(str.isdigit, q_val))) > 1: is_master_header = True
            except: pass
            if is_master_header:
                header_row = row; continue 
            row = sanitize_row_data(row)
            d_name = clean_driver_name(row.get('DRIVER', ''))
            t_val = str(row.get('TIME', '')).lower()
            has_time = pd.notna(row.get('TIME')) and (any(c.isdigit() for c in t_val) or "segera" in t_val)
            if not str(row.get('PLATE', '')) or str(row.get('PLATE', '')).lower() == 'nan':
                search_text = str(row.get('Original_Text', '')) + " " + str(row.get('DRIVER', ''))
                found_plate = extract_plate_aggressive(search_text)
                if found_plate: row['PLATE'] = found_plate
            has_plate = pd.notna(row.get('PLATE')) and len(str(row.get('PLATE'))) > 3
            if d_name or has_time or has_plate:
                row['DRIVER'] = d_name; valid_candidates.append(row)
        if header_row is None and len(block_data) > 0: header_row = block_data.iloc[0]
        for i in range(target_qty):
            if i < len(valid_candidates):
                candidate = valid_candidates[i]
                for col in ['ORIGIN', 'DESTINATION', 'UNIT_TYPE', 'DATE']:
                    val = candidate.get(col)
                    if pd.isna(val) or str(val).strip() == "":
                        header_val = header_row.get(col)
                        if col == 'DATE':
                            if header_val and (re.search(r'\d', str(header_val))): candidate[col] = header_val
                        else: candidate[col] = header_val
                final_rows.append(candidate)
            else:
                clean_slot = header_row.copy()
                clean_slot['DRIVER'] = ""; clean_slot['PLATE'] = ""; clean_slot['PHONE'] = ""; clean_slot['TIME'] = ""; clean_slot['UNIT_QTY'] = 1
                if header_row.get('DATE') and re.search(r'\d', str(header_row.get('DATE'))): clean_slot['DATE'] = header_row['DATE']
                else: clean_slot['DATE'] = ""
                final_rows.append(clean_slot)
    return pd.DataFrame(final_rows).reset_index(drop=True)

def apply_revision_logic(df_final):
    """
    Tangani revisi order. Deteksi row dengan kata kunci 'rev', 'revisi', 'update'
    dan terapkan field updates ke row yang TIME-nya sama. Hapus revision row dari output.
    Format TIME bisa 08:00 atau 08.00, semua akan dinormalisasi untuk matching.
    """
    if df_final is None or df_final.empty:
        return df_final

    rows_to_update = []
    rows_to_remove = []

    # Helper: normalisasi format waktu (08:00 dan 08.00 menjadi sama)
    def normalize_time(time_str):
        if not time_str:
            return None
        time_str = str(time_str).strip()
        # Replace . dengan : untuk normalisasi
        time_str = time_str.replace('.', ':')
        return time_str

    # Helper: ekstrak field dari Original_Text jika belum ada di DataFrame
    def extract_field_from_text(original_text, field_name):
        """Ekstrak field dari Original_Text dengan pattern matching."""
        if not original_text:
            return None

        text_lower = str(original_text).lower()

        if field_name == 'PLATE':
            # Cari pattern: "nopol : ...", "plat : ...", "no plat : ..."
            patterns = [
                r'nopol\s*:\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})',
                r'no\.?\s*plat\s*:\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})',
                r'plat\s*:\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})',
            ]
            for pattern in patterns:
                match = re.search(pattern, original_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        elif field_name == 'DRIVER':
            # Cari pattern: "driver : ...", "pengemudi : ..."
            patterns = [
                r'driver\s*:\s*([^\n:]+)',
                r'pengemudi\s*:\s*([^\n:]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, original_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        elif field_name == 'PHONE':
            # Cari pattern: "no hp : ...", "no. hp : ...", "kontak : ..."
            patterns = [
                r'no\.?\s*hp\s*:\s*(\d+)',
                r'no\.?\s*telp\s*:\s*(\d+)',
                r'kontak\s*:\s*(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, original_text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        return None

    for idx, row in df_final.iterrows():
        original_text = str(row.get('Original_Text', '')).lower()

        # Deteksi kata kunci revisi (case insensitive)
        if not any(keyword in original_text for keyword in ['rev', 'revisi', 'update']):
            continue

        # Ekstrak target time dalam format HH:MM atau HH.MM (bisa "jam 08:00" atau "jam 08.00")
        # Pattern: cari "jam HH:MM" atau "jam HH.MM" atau langsung HH:MM atau HH.MM
        time_match = re.search(r'jam\s+(\d{1,2})[:.](\d{2})', original_text)
        if not time_match:
            # Fallback: cari hanya HH:MM atau HH.MM tanpa "jam"
            time_match = re.search(r'(\d{1,2})[:.](\d{2})', original_text)

        if not time_match:
            continue

        # Format target time dengan colon
        target_time = f"{time_match.group(1)}:{time_match.group(2)}"
        target_time_normalized = normalize_time(target_time)

        # Kumpulkan updates untuk target_time ini
        updates = {}
        original_text_full = str(row.get('Original_Text', ''))  # Keep original case untuk ekstraksi

        for field in ['PLATE', 'DRIVER', 'PHONE']:
            val = row.get(field)
            # Try dari field di DataFrame dulu
            if pd.notna(val) and str(val).strip():
                updates[field] = val
            else:
                # Fallback: ekstrak dari Original_Text
                extracted = extract_field_from_text(original_text_full, field)
                if extracted:
                    updates[field] = extracted

        if updates:
            rows_to_update.append((target_time_normalized, updates))

        # Tandai revision row untuk dihapus
        rows_to_remove.append(idx)

    # Terapkan updates ke row yang TIME-nya matching (dengan normalisasi)
    for target_time_normalized, updates in rows_to_update:
        for row_idx in df_final.index:
            if row_idx not in rows_to_remove:  # Skip revision rows
                df_time = normalize_time(df_final.loc[row_idx, 'TIME'])
                if df_time == target_time_normalized:
                    for field, value in updates.items():
                        df_final.loc[row_idx, field] = value

    # Hapus revision rows
    df_final = df_final.drop(rows_to_remove)
    return df_final.reset_index(drop=True)

def format_date_custom(date_input):
    """Format tanggal ke format Indonesia (DD BULAN TAHUN) untuk laporan Rafay."""
    try:
        if pd.isna(date_input) or str(date_input).strip() == "": return ""
        date_str = str(date_input).strip()
        date_str = re.sub(r'[^\w\s/\-]', '', date_str)
        indo_months = {1: 'JANUARI', 2: 'FEBRUARI', 3: 'MARET', 4: 'APRIL', 5: 'MEI', 6: 'JUNI', 7: 'JULI', 8: 'AGUSTUS', 9: 'SEPTEMBER', 10: 'OKTOBER', 11: 'NOVEMBER', 12: 'DESEMBER'}
        day, month, year = None, None, None
        match_digit = re.search(r'(\d{1,2})[/\-\s]+(\d{1,2})[/\-\s]+(\d{4})', date_str)
        if match_digit:
            day, month, year = int(match_digit.group(1)), int(match_digit.group(2)), int(match_digit.group(3))
        else:
            month_map = {'jan': 1, 'feb': 2, 'peb': 2, 'mar': 3, 'apr': 4, 'mei': 5, 'may': 5, 'jun': 6, 'jul': 7, 'agu': 8, 'aug': 8, 'sep': 9, 'okt': 10, 'oct': 10, 'nov': 11, 'des': 12, 'dec': 12}
            clean_str = date_str.lower()
            for k, v in month_map.items():
                if k in clean_str: month = v; break
            if month:
                match_year = re.search(r'\d{4}', clean_str)
                if match_year: year = int(match_year.group(0))
                # FIX: Find day closest to month keyword (not just first number)
                # Look for day that appears immediately before the month name
                month_text = None
                for k, v in month_map.items():
                    if k in clean_str:
                        month_text = k
                        break
                if month_text:
                    # Find all numbers in the string
                    all_numbers = [(m.start(), int(m.group(0))) for m in re.finditer(r'\b\d{1,2}\b', clean_str)]
                    month_pos = clean_str.find(month_text)
                    if all_numbers and month_pos >= 0:
                        # Find the number closest to (and before) the month text
                        candidates = [num for pos, num in all_numbers if pos < month_pos]
                        if candidates:
                            # Take the last (closest) number before month
                            day = candidates[-1]
                        elif all_numbers:
                            # If no numbers before month, take first number overall
                            day = all_numbers[0][1]
                else:
                    # Fallback: just get first number if no month found
                    match_day = re.search(r'\b\d{1,2}\b', clean_str)
                    if match_day: day = int(match_day.group(0))
        if day and month and year:
            day_str = str(day).zfill(2)
            month_str = indo_months.get(month, "")
            if month_str: return f"{day_str} {month_str} {year}"
        return date_str
    except: return str(date_input)

def clean_destination_format(text):
    """Normalisasi format tujuan untuk konsistensi laporan Rafay (uppercase, delimiter konsisten)."""
    if pd.isna(text): return ""
    # Data sudah dinormalisasi oleh normalize_route() di sanitize_row_data()
    # Hanya perlu uppercase dan trim, tanpa re-processing
    return str(text).upper().strip()

def calculate_extraction_accuracy(df_raw, df_final):
    """
    Hitung akurasi ekstraksi REAL berdasarkan kelengkapan data.
    Akurasi = (entitas yang berhasil diisi / total entitas) * 100
    """
    if df_final is None or df_final.empty:
        return 0.0

    critical_fields = ['DRIVER', 'PLATE', 'DATE', 'TIME', 'ORIGIN', 'DESTINATION', 'UNIT_TYPE']
    total_fields = len(critical_fields) * len(df_final)
    filled_fields = 0

    for field in critical_fields:
        if field in df_final.columns:
            filled_fields += df_final[field].notna().sum()

    accuracy = round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0.0
    return min(accuracy, 100.0)  # Cap at 100%

def calculate_confidence_score(df):
    """
    Hitung confidence score untuk setiap baris berdasarkan kelengkapan data.
    Score simulasi (0.0 - 1.0) didasarkan pada:
    - No. Plat (>3 chars): +0.4
    - Driver (ada): +0.3
    - Tujuan (ada): +0.2
    - Tgl Muat (ada): +0.1
    """
    scores = []
    for _, row in df.iterrows():
        score = 0.0

        # Check No. Plat (Column: PLATE dalam raw, atau No. Plat dalam office)
        plate_key = 'No. Plat' if 'No. Plat' in df.columns else 'PLATE'
        plate_val = str(row.get(plate_key, '')).strip() if plate_key in df.columns else ""
        if len(plate_val) > 3:
            score += 0.4

        # Check Driver
        driver_key = 'Driver' if 'Driver' in df.columns else 'DRIVER'
        driver_val = str(row.get(driver_key, '')).strip() if driver_key in df.columns else ""
        if driver_val and driver_val.lower() != 'nan':
            score += 0.3

        # Check Tujuan (Column: DESTINATION dalam raw, atau Tujuan dalam office)
        tujuan_key = 'Tujuan' if 'Tujuan' in df.columns else 'DESTINATION'
        tujuan_val = str(row.get(tujuan_key, '')).strip() if tujuan_key in df.columns else ""
        if tujuan_val and tujuan_val.lower() != 'nan':
            score += 0.2

        # Check Tgl Muat (Column: DATE dalam raw, atau Tgl Muat dalam office)
        tgl_key = 'Tgl Muat' if 'Tgl Muat' in df.columns else 'DATE'
        tgl_val = str(row.get(tgl_key, '')).strip() if tgl_key in df.columns else ""
        if tgl_val and tgl_val.lower() != 'nan':
            score += 0.1

        scores.append(round(min(score, 1.0), 3))

    return scores

# =================================================================================
# --- FRONTEND UI: WHITE THEME - PROFESSIONAL EDITION ---
# =================================================================================

st.set_page_config(page_title="Rafay Logistics IDP v2.0", layout="wide", initial_sidebar_state="collapsed")

# GLOBAL CSS INJECTION - WHITE THEME PROFESSIONAL
st.markdown("""
    <style>
        /* Base Colors & Fonts - Rafay White Professional Theme */
        :root {
            --bg-color: #FFFFFF;
            --card-bg: #F8F9FA;
            --border-color: #E1E4E8;
            --accent-color: #0F766E;
            --text-main: #1F2937;
            --text-muted: #6B7280;
            --success-color: #10B981;
        }
        
        .stApp {
            background-color: var(--bg-color) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--text-main) !important;
        }

        /* Hiding Streamlit Defaults */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container { padding-top: 2rem !important; max-width: 1400px; }

        /* HEADER SECTION */
        .top-navbar {
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 2px solid var(--border-color); padding-bottom: 20px; margin-bottom: 30px;
        }
        .nav-logo { display: flex; align-items: center; gap: 15px; }
        .nav-title { font-size: 1.5rem; font-weight: 700; color: var(--text-main); margin: 0; line-height: 1.2; }
        .nav-subtitle { font-size: 0.9rem; color: var(--text-muted); margin: 5px 0 0 0; font-weight: 500; }
        .nav-accent { color: var(--accent-color); font-weight: 700; }
        .nav-status { display: flex; gap: 20px; }
        .status-badge {
            background-color: white; border: 1.5px solid var(--border-color);
            padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; color: var(--text-muted);
            display: flex; align-items: center; gap: 8px; font-weight: 600;
        }
        .status-dot { width: 8px; height: 8px; background-color: var(--success-color); border-radius: 50%; }

        /* METRIC CARDS */
        .metrics-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;
        }
        .m-card {
            background-color: white; border: 1.5px solid var(--border-color);
            border-radius: 8px; padding: 20px; display: flex; align-items: center; gap: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .m-icon {
            background-color: rgba(15, 118, 110, 0.1); padding: 12px; border-radius: 8px; color: var(--accent-color);
        }
        .m-content p { margin: 0; font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
        .m-content h4 { margin: 8px 0 0 0; font-size: 1.5rem; color: var(--text-main); font-weight: 700;}

        /* PIPELINE */
        .pipeline-card {
            background-color: white; border: 1.5px solid var(--border-color);
            border-radius: 8px; padding: 25px; margin-bottom: 30px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .pipeline-title { font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin-bottom: 25px; display: flex; align-items: center; gap: 10px;}
        .pipeline-steps {
            display: flex; justify-content: space-between; align-items: center;
        }
        .step-item {
            background-color: var(--card-bg); border: 1px solid var(--border-color);
            padding: 15px 20px; border-radius: 6px; text-align: center; width: 16%;
        }
        .step-item svg { color: var(--accent-color); width: 24px; margin-bottom: 10px; }
        .step-item p { margin: 0; font-size: 0.85rem; color: var(--text-main); font-weight: 600; }
        .step-item span { font-size: 0.75rem; color: var(--text-muted); display: block; margin-top: 5px; }
        .arrow { color: var(--border-color); font-weight: bold; font-size: 1.2rem;}

        /* INPUT PANEL */
        .input-panel {
            background-color: white; border: 1.5px solid var(--border-color);
            border-radius: 8px; padding: 20px; height: 100%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .panel-header { display: flex; align-items: center; gap: 10px; font-weight: 700; color: var(--text-main); margin-bottom: 15px; }
        .badge-ml { background-color: rgba(15, 118, 110, 0.1); color: var(--accent-color); font-size: 0.65rem; padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(15, 118, 110, 0.2); font-weight: 600; }
        
        .tab-mockup { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab-btn { background-color: white; border: 1.5px solid var(--border-color); color: var(--text-main); padding: 8px 15px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; width: 50%; text-align: center; cursor: default; }
        .tab-inactive { background-color: var(--card-bg); color: var(--text-muted); }
        
        /* Text Area overrides */
        .stTextArea textarea {
            background-color: white !important; color: var(--text-main) !important; border: 1.5px solid var(--border-color) !important;
            border-radius: 6px !important; font-family: 'Courier New', monospace; font-size: 0.85rem; padding: 12px;
        }
        .stTextArea textarea:focus { border-color: var(--accent-color) !important; box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1) !important;}
        
        /* Button overrides */
        div.stButton > button {
            background-color: var(--accent-color) !important; color: white !important; border: none !important;
            border-radius: 6px !important; padding: 12px 16px !important; font-weight: 600 !important; width: 100% !important; margin-top: 15px; transition: 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover { background-color: #0D5D56 !important; color: white !important; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }

        /* Output Placeholder */
        .output-panel {
            background-color: white; border: 1.5px solid var(--border-color);
            border-radius: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 500px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .out-icon { background-color: rgba(15, 118, 110, 0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px; position: relative; }
        .out-icon svg { width: 40px; color: var(--accent-color); }
        .out-badge { position: absolute; bottom: -5px; right: -5px; background: var(--accent-color); color: white; font-size: 0.6rem; font-weight: 700; padding: 4px 8px; border-radius: 4px; }
        .out-title { color: var(--text-main); font-weight: 700; font-size: 1.2rem; margin-bottom: 10px; }
        .out-desc { color: var(--text-muted); font-size: 0.85rem; text-align: center; max-width: 400px; line-height: 1.6; margin-bottom: 30px; }
        
        .out-options { display: flex; gap: 15px; }
        .opt-box { background: var(--card-bg); border: 1px solid var(--border-color); padding: 12px 20px; border-radius: 6px; text-align: center; }
        .opt-box p { margin: 0; color: var(--text-main); font-weight: 600; font-size: 0.85rem; }
        .opt-box span { color: var(--text-muted); font-size: 0.7rem; display: block; margin-top: 3px; }

        /* Dataframe Overrides - Full White Theme */
        [data-testid="stDataFrame"] { 
            background-color: white !important; 
        }
        
        /* Table styling complete */
        .stDataFrame {
            background-color: white !important;
        }
        
        /* Table container */
        [data-testid="stDataFrame"] > div {
            background-color: white !important;
        }
        
        /* Table cells - text color */
        [data-testid="stDataFrame"] tbody td {
            color: var(--text-main) !important;
            background-color: white !important;
            border-color: var(--border-color) !important;
        }
        
        /* Table header */
        [data-testid="stDataFrame"] thead th {
            background-color: #F0F4F4 !important;
            color: var(--text-main) !important;
            border-color: var(--border-color) !important;
            font-weight: 600;
        }
        
        /* Table rows alternating (zebra stripe) */
        [data-testid="stDataFrame"] tbody tr:nth-child(odd) {
            background-color: white !important;
        }
        
        [data-testid="stDataFrame"] tbody tr:nth-child(even) {
            background-color: #FAFBFC !important;
        }
        
        /* Table borders */
        [data-testid="stDataFrame"] table {
            border-color: var(--border-color) !important;
            border-collapse: collapse;
        }
        
        [data-testid="stDataFrame"] th, 
        [data-testid="stDataFrame"] td {
            border-color: var(--border-color) !important;
            padding: 10px 12px;
        }
        
        /* Hover effect for rows */
        [data-testid="stDataFrame"] tbody tr:hover {
            background-color: rgba(15, 118, 110, 0.08) !important;
        }
        
        /* Table scroll styling */
        [data-testid="stDataFrame"] ::-webkit-scrollbar {
            height: 8px;
            width: 8px;
        }
        
        [data-testid="stDataFrame"] ::-webkit-scrollbar-track {
            background: var(--card-bg);
        }
        
        [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        
        [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
            background: #C4C7C7;
        }
        
        /* Download Button Styling */
        div.stDownloadButton > button {
            background-color: var(--success-color) !important; color: white !important; border: none !important;
            border-radius: 6px !important; font-weight: 600 !important; width: 100% !important; margin-top: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div.stDownloadButton > button:hover { background-color: #059669 !important; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }

        /* Result Container */
        .result-container {
            background-color: white; padding: 25px; border-radius: 8px; border: 1.5px solid var(--border-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .result-header { color: var(--text-main); font-weight: 700; font-size: 1.1rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }

        /* Simple animation for processing */
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* PERFORMANCE DASHBOARD - METRIC BOXES */
        .dashboard-container {
            width: 100%;
            margin-bottom: 20px;
        }

        .metric-box {
            background-color: #F8FAFC;
            border: 1.5px solid #E2E8F0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .metric-box-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .metric-box-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1B6987;
            line-height: 1.2;
        }

        /* DIVIDER */
        .dashboard-divider {
            height: 1.5px;
            background-color: #E2E8F0;
            margin: 30px 0;
        }

        /* RESULT TABLE CONTAINER */
        .result-table-container {
            margin-top: 20px;
        }

    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_processor(): return ChatBatchProcessor()

def render_top_ui(proses_waktu="--", baris="--", akurasi="--"):
    """Render header Rafay IDP dengan status real-time dan metrics pipeline."""
    st.markdown(f"""
        <div class="top-navbar">
            <div class="nav-logo">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-color)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 1 0 0-20z"></path><path d="M12 6v6l4 2"></path></svg>
                <div>
                    <h1 class="nav-title">Rafay Logistics <span class="nav-accent">IDP</span></h1>
                    <p class="nav-subtitle">Intelligent Document Processing v2.0 (IndobERT + LayoutLMv3)</p>
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
    """Main aplikasi Rafay IDP - antarmuka ekstraksi data logistik."""

    if 'waktu' not in st.session_state: st.session_state.waktu = "--"
    if 'baris' not in st.session_state: st.session_state.baris = "--"
    if 'akurasi' not in st.session_state: st.session_state.akurasi = "--"
    if 'avg_confidence' not in st.session_state: st.session_state.avg_confidence = 0.0
    if 'processing_time' not in st.session_state: st.session_state.processing_time = 0.0
    
    render_top_ui(st.session_state.waktu, st.session_state.baris, st.session_state.akurasi)
    
    col_left, col_right = st.columns([1, 1.5], gap="large")
    
    with col_left:
        st.markdown("""
        <div class="input-panel">
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

        # Advanced Job Number Configuration
        st.markdown("**Konfigurasi Job Number**")
        col_job1, col_job2, col_job3, col_job4 = st.columns(4, gap="small")

        with col_job1:
            job_start = st.number_input(
                "Nomor",
                value=st.session_state.get('job_start', 1),
                min_value=1,
                step=1,
                help="Nomor awal"
            )
            st.session_state['job_start'] = job_start

        with col_job2:
            job_company = st.text_input(
                "Company",
                value=st.session_state.get('job_company', 'JNE'),
                max_chars=6,
                help="Nama perusahaan (JNE, JNT, RAFAY, dll)"
            )
            st.session_state['job_company'] = job_company.upper()

        with col_job3:
            month_options = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
            month_idx = month_options.index(st.session_state.get('job_month', 'II')) if st.session_state.get('job_month', 'II') in month_options else 1
            job_month = st.selectbox(
                "Bulan",
                month_options,
                index=month_idx,
                help="Bulan (I=Januari, II=Februari, dll)"
            )
            st.session_state['job_month'] = job_month

        with col_job4:
            job_year = st.number_input(
                "Tahun",
                value=st.session_state.get('job_year', 2026),
                min_value=2000,
                max_value=2100,
                step=1,
                help="Tahun"
            )
            st.session_state['job_year'] = job_year

        # Live preview
        preview_format = f"{job_start:03d}/{job_company.upper()}-RAFAY/{job_month}/{job_year}"
        st.markdown(f"<span style='font-size:0.9rem; color:#666;'>Preview: <code>{preview_format}</code></span>", unsafe_allow_html=True)

        chat_input = st.text_area(
            "Input",
            height=300,
            label_visibility="collapsed",
            placeholder="Paste data chat WhatsApp atau dokumen logistik di sini...\n\nContoh Format:\n[08.30, 15/2/2026] Driver Budi: Waktu loading\n: 10.00 15/2/2026\nTujuan : Jakarta - Surabaya\nUnit : CDD\nPlat : B 1234 CD\nDriver : Budi\nHP : 081234567890"
        )

        st.markdown("<p style='font-size:0.8rem; color:#6B7280; margin-top:10px;'>Siap menerima input dokumen logistik...</p>", unsafe_allow_html=True)
        btn = st.button("Mulai Ekstraksi Data")

    with col_right:
        if not btn and 'df_office' not in st.session_state:
            st.markdown("""
            <div class="output-panel">
                <div class="out-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    <div class="out-badge">AI</div>
                </div>
                <div class="out-title">Siap Memproses Data</div>
                <div class="out-desc">Input dokumen logistik Rafay (chat WA, SMS, atau PDF) pada panel input, lalu klik Mulai Ekstraksi untuk memproses dengan IndobERT + LayoutLMv3.</div>
                <div class="out-options">
                    <div class="opt-box"><p>WhatsApp</p><span>Chat Parse</span></div>
                    <div class="opt-box"><p>Dokumen</p><span>OCR + Layout</span></div>
                    <div class="opt-box"><p>Excel</p><span>Auto Report</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        if btn:
            if not chat_input.strip():
                st.error("Input kosong. Silakan paste data dokumen terlebih dahulu.")
            else:
                # Create processing container
                processing_container = st.empty()
                
                start_time = time.time()
                
                # Step 1: Format
                with processing_container.container():
                    st.markdown("""
                    <div style='background-color: white; border: 1.5px solid #E1E4E8; border-radius: 8px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>
                        <div style='font-size: 1rem; font-weight: 700; color: #1F2937; margin-bottom: 15px;'>Memformat input data...</div>
                    """, unsafe_allow_html=True)
                    st.progress(0.15)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                formatted_input = auto_format_chat_input(chat_input)

                time.sleep(0.15)

                # Step 2: Extract
                with processing_container.container():
                    st.markdown("""
                    <div style='background-color: white; border: 1.5px solid #E1E4E8; border-radius: 8px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>
                        <div style='font-size: 1rem; font-weight: 700; color: #1F2937; margin-bottom: 15px;'>Mengekstraksi data dengan IndobERT + LayoutLMv3...</div>
                    """, unsafe_allow_html=True)
                    st.progress(0.45)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                temp_path = "temp.txt"
                with open(temp_path, "w", encoding="utf-8") as f: 
                    f.write(formatted_input)
                
                df_raw = get_processor().process_file(temp_path)

                time.sleep(0.15)

                if df_raw is not None and not df_raw.empty:
                    # Step 3: Preprocess
                    with processing_container.container():
                        st.markdown("""
                        <div style='background-color: white; border: 1.5px solid #E1E4E8; border-radius: 8px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>
                            <div style='font-size: 1rem; font-weight: 700; color: #1F2937; margin-bottom: 15px;'>Memproses dan validasi data...</div>
                        """, unsafe_allow_html=True)
                        st.progress(0.70)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    df_proc = preprocess_context(df_raw)
                    df_final = enforce_block_quota(df_proc)

                    accuracy = calculate_extraction_accuracy(df_raw, df_final)
                    time.sleep(0.15)
                    
                    # Step 4: Generate
                    with processing_container.container():
                        st.markdown("""
                        <div style='background-color: white; border: 1.5px solid #E1E4E8; border-radius: 8px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'>
                            <div style='font-size: 1rem; font-weight: 700; color: #1F2937; margin-bottom: 15px;'>Memformat laporan Excel...</div>
                        """, unsafe_allow_html=True)
                        st.progress(0.90)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    df_office = pd.DataFrame()
                    df_office['No.'] = range(1, len(df_final) + 1)

                    # Get custom job number configuration from session state
                    job_start = st.session_state.get('job_start', 1)
                    job_company = st.session_state.get('job_company', 'JNE').upper()
                    job_month = st.session_state.get('job_month', 'II')
                    job_year = st.session_state.get('job_year', 2026)

                    df_office['Job Number'] = [f"{job_start+i:03d}/{job_company}-RAFAY/{job_month}/{job_year}" for i in range(len(df_final))]

                    df_office['Tgl RO'] = "" 
                    df_office['Tgl Muat'] = df_final['DATE'].apply(format_date_custom)
                    df_office['Vendor'] = ""
                    df_office['Pickup'] = df_final['ORIGIN'].str.upper()
                    df_office['Tujuan'] = df_final['DESTINATION'].apply(clean_destination_format)
                    df_office['No. Plat'] = df_final['PLATE'].str.upper()
                    df_office['Type Truck'] = df_final['UNIT_TYPE'].str.upper()
                    df_office['Driver'] = df_final['DRIVER'].fillna("").astype(str).str.title()
                    df_office['Kontak Driver'] = df_final['PHONE']
                    df_office['Jam Loading'] = df_final['TIME']

                    # Calculate confidence scores for each row
                    confidence_scores = calculate_confidence_score(df_office)
                    avg_confidence = round((sum(confidence_scores) / len(confidence_scores)) * 100, 1) if confidence_scores else 0.0
                    df_office['Confidence'] = confidence_scores

                    time.sleep(0.15)

                    end_time = time.time()
                    processing_time = round(end_time - start_time, 2)

                    # Complete
                    processing_container.empty()

                    st.session_state['df_office'] = df_office
                    st.session_state.waktu = f"{processing_time}s"
                    st.session_state.baris = f"{len(df_office)} Order"
                    st.session_state.akurasi = f"{accuracy}%"
                    st.session_state.avg_confidence = avg_confidence
                    st.session_state.processing_time = processing_time

                    time.sleep(0.3)
                    st.rerun()
                    
                else:
                    processing_container.empty()
                    st.error("Ekstraksi data gagal. Silakan periksa format input dokumen.")
                    
                if os.path.exists(temp_path): 
                    os.remove(temp_path)
                    
        if 'df_office' in st.session_state:
            # Performance Dashboard Container
            dashboard_col1, dashboard_col2, dashboard_col3 = st.columns(3, gap="medium")

            with dashboard_col1:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-box-label">Model Confidence</div>
                    <div class="metric-box-value">{st.session_state.get('avg_confidence', 0.0)}%</div>
                </div>
                """, unsafe_allow_html=True)

            with dashboard_col2:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-box-label">Processing Time</div>
                    <div class="metric-box-value">{st.session_state.get('processing_time', 0.0)}s</div>
                </div>
                """, unsafe_allow_html=True)

            with dashboard_col3:
                st.markdown(f"""
                <div class="metric-box">
                    <div class="metric-box-label">Total Records</div>
                    <div class="metric-box-value">{len(st.session_state['df_office'])}</div>
                </div>
                """, unsafe_allow_html=True)

            # Visual Separator
            st.divider()

            # Result Table Container
            st.markdown("<div class='result-container'>", unsafe_allow_html=True)
            st.markdown("<div class='result-header'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='3' y1='9' x2='21' y2='9'></line><line x1='9' y1='21' x2='9' y2='9'></line></svg>Hasil Ekstraksi & Validasi</div>", unsafe_allow_html=True)
            st.dataframe(st.session_state['df_office'], use_container_width=True)
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                st.session_state['df_office'].to_excel(writer, index=False, sheet_name='Laporan')
                wb = writer.book
                ws = writer.sheets['Laporan']
                
                h_fmt = wb.add_format({
                    'bold': True, 
                    'bg_color': '#0F766E', 
                    'font_color': 'white', 
                    'border': 1, 
                    'align': 'center',
                    'valign': 'vcenter'
                })
                b_fmt = wb.add_format({
                    'border': 1, 
                    'valign': 'vcenter'
                })
                
                for c, val in enumerate(st.session_state['df_office'].columns): 
                    ws.write(0, c, val, h_fmt)
                
                ws.set_column('A:A', 5)
                ws.set_column('B:K', 18)
                
                for r in range(len(st.session_state['df_office'])):
                    for c in range(len(st.session_state['df_office'].columns)):
                        val = st.session_state['df_office'].iloc[r, c]
                        ws.write(r+1, c, "" if pd.isna(val) else val, b_fmt)

            st.download_button(
                label="Download Laporan Excel Rafay",
                data=buffer.getvalue(),
                file_name=f"Rafay_IDP_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
            )
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()