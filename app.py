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

    pattern_with_date = r"(?i)(Waktu loading\s*:\s*)(.*?)(\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}|\s+\d{1,2}\s+[a-zA-Z]+\s+\d{4})"
    date_header_pattern = r"(?:REQUEST|ONCALL|TAMBAHAN).*?(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
    waktu_loading_standalone = r"(?i)Waktu\s+loading\s*:\s*(.+?)(?=\n|$)"

    current_global_date = ""
    current_block_date = ""
    current_header_timestamp = None 

    for line in lines:
        header_timestamp_pattern = r'\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
        timestamp_match = re.search(header_timestamp_pattern, line)
        if timestamp_match:
            current_header_timestamp = timestamp_match.group(2)
            current_global_date = current_header_timestamp
            current_block_date = current_header_timestamp
            formatted_lines.append(line)
            continue

        is_request_header = re.search(r"(?i)(?:REQUEST|ONCALL|TAMBAHAN)", line)
        if is_request_header:
            header_match = re.search(date_header_pattern, line, re.IGNORECASE)
            if header_match:
                current_global_date = header_match.group(1)
                current_block_date = current_global_date
            formatted_lines.append(line)
            continue

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

        standalone_match = re.search(waktu_loading_standalone, line, re.IGNORECASE)
        if standalone_match:
            jam_raw = standalone_match.group(1).strip()
            date_in_value = re.search(r'(\d{1,2}[./:-]\d{1,2}[./:-]\d{4})', jam_raw)
            if date_in_value:
                jam_part = jam_raw[:date_in_value.start()].strip()
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

def normalize_phone_number(phone):
    if pd.isna(phone) or not str(phone).strip(): return ""
    phone_digits = re.sub(r'\D', '', str(phone))
    if not phone_digits: return ""
    if phone_digits.startswith('62'): phone_digits = '0' + phone_digits[2:]
    return phone_digits

def normalize_route(text):
    if pd.isna(text) or not str(text).strip(): return ""
    text_str = str(text).strip()
    if text_str.lower() in ['none', 'nan', 'nat']: return ""
    route = text_str.upper()
    route = route.replace('–', '-').replace('/', '-')
    route = re.sub(r'\s+', ' ', route)
    if '-' in route or ',' in route:
        route = route.replace(',', '-')
        parts = [p.strip() for p in route.split('-') if p.strip()]
        if len(parts) >= 2: return ', '.join(parts)
    if ' ' in route:
        parts = [p.strip() for p in route.split() if p.strip()]
        if len(parts) > 1: return ', '.join(parts)
    return route.strip()

def clean_driver_name(name):
    if not name or pd.isna(name) or str(name).lower() == 'none': return ""
    clean_name = str(name).strip().title()
    for bad_word in DRIVER_BLACKLIST:
        if bad_word.lower() in clean_name.lower(): return ""
    return clean_name

def sanitize_row_data(row):
    d = str(row.get('DATE', '')).strip()
    t = str(row.get('TIME', '')).strip()
    orig_text = str(row.get('Original_Text', '')).strip()
    drv = str(row.get('DRIVER', '')).strip()

    if d.lower() in ['none', 'nan', 'nat']: d = ""
    if t.lower() in ['none', 'nan', 'nat']: t = ""

    has_segera = False
    if "segera" in t.lower(): has_segera = True
    elif "segera" in d.lower(): has_segera = True; d = ""
    elif "segera" in drv.lower(): has_segera = True
    elif "segera" in orig_text.lower(): has_segera = True

    if has_segera:
        t = "SEGERA"
    else:
        time_in_date_pattern = r'^(\d{1,2}:\d{2})\s+(.+)$'
        time_in_date_match = re.search(time_in_date_pattern, d)
        if time_in_date_match:
            potential_time = time_in_date_match.group(1)
            remaining_date = time_in_date_match.group(2)
            if not t or t in ["SEGERA", ""]:
                t = potential_time
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
        raw_phone = str(row.get('PHONE', '')).strip()
        if raw_phone and raw_phone.lower() not in ['none', 'nan', 'nat', '']:
            row['PHONE'] = normalize_phone_number(raw_phone)
        else:
            row['PHONE'] = ""
    
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
    if df is None or df.empty: return df
    df = repair_headers(df)
    df = mark_order_block(df)
    required_cols = ['UNIT_TYPE', 'ORIGIN', 'DESTINATION', 'DATE']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    for col in required_cols:
        df[col] = df.groupby('BLOCK_ID')[col].ffill()
    return df

def enforce_block_quota(df):
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

# --- [FITUR BARU] REVISI PINTAR BERBASIS MEMORI ---
def apply_revisions_from_chat(chat_text, df_final):
    """
    Menangkap pesan revisi langsung dari teks asli chat WhatsApp dan 
    menerapkannya berdasarkan kecocokan Jam atau Memory Timestamp chat.
    """
    if df_final is None or df_final.empty or not chat_text:
        return df_final
        
    df = df_final.copy()
    wa_pattern = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
    messages = re.split(wa_pattern, chat_text)
    
    def normalize_time(time_str):
        if not time_str: return None
        s = str(time_str).strip().replace('.', ':')
        m = re.search(r'(\d{1,2}):(\d{2})', s)
        if m: return f"{int(m.group(1)):02d}:{m.group(2)}"
        return None
        
    # 1. Peta Memori: Ingat setiap plat dikirim jam berapa di header WA
    plate_to_msg_time = {}
    
    for msg in messages:
        header_match = re.search(r'\[(\d{2}[.,:]\d{2})\s*,', msg)
        if header_match:
            msg_time = normalize_time(header_match.group(1))
            plates = re.findall(r'(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:?\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})', msg, re.IGNORECASE)
            for p in plates:
                plate_clean = p.strip().upper()
                # Hanya ingat pesan yang BUKAN pesan revisi
                if not any(kw in msg.lower() for kw in ['rev', 'revisi', 'update', 'ganti']):
                    plate_to_msg_time[plate_clean] = msg_time
                    
    # 2. Cari instruksi revisi
    for msg in messages:
        msg_lower = msg.lower()
        if any(kw in msg_lower for kw in ['rev', 'revisi', 'update', 'ganti']):
            target_time_match = re.search(r'(?:jam|pukul|waktu)\s+(\d{1,2}[:.]\d{2})', msg_lower)
            target_time = normalize_time(target_time_match.group(1)) if target_time_match else None
            
            updates = {}
            lines = msg.split('\n')
            for line in lines:
                line_lower = line.lower()
                if ':' in line or 'adalah' in line_lower or line_lower.startswith('nopol') or line_lower.startswith('plat'):
                    plate_match = re.search(r'(?:nopol|no\.?\s*pol(?:isi)?|no\.?\s*plat|plat)\s*:?\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})', line, re.IGNORECASE)
                    if plate_match:
                        updates['PLATE'] = plate_match.group(1).strip().upper()
                        
                    driver_match = re.search(r'(?:driver|pengemudi)\s*:?\s*([a-zA-Z\s]+)', line, re.IGNORECASE)
                    if driver_match and not any(kw in driver_match.group(1).lower() for kw in ['rev', 'revisi']):
                        d_name = clean_driver_name(driver_match.group(1).strip())
                        if d_name: updates['DRIVER'] = d_name
                        
                    phone_match = re.search(r'(?:no\.?\s*hp|hp|no\.?\s*telp|kontak)\s*:?\s*([0-9+\-\s]+)', line, re.IGNORECASE)
                    if phone_match:
                        updates['PHONE'] = normalize_phone_number(phone_match.group(1).strip())
            
            # 3. Terapkan update ke dataframe
            if target_time and updates:
                for idx, row in df.iterrows():
                    # Coba cari jam yang terekstrak eksplisit
                    row_time = normalize_time(row.get('TIME', ''))
                    
                    # Jika TIME kosong, gunakan Memory Map (Tanya memori: Plat ini dulu dikirim jam berapa?)
                    if not row_time:
                        row_plate = str(row.get('PLATE', '')).strip().upper()
                        row_time = plate_to_msg_time.get(row_plate)
                        
                    if row_time == target_time:
                        if 'PLATE' in updates: df.at[idx, 'PLATE'] = updates['PLATE']
                        if 'DRIVER' in updates: df.at[idx, 'DRIVER'] = updates['DRIVER']
                        if 'PHONE' in updates: df.at[idx, 'PHONE'] = updates['PHONE']
                        
            elif updates and len(df) == 1:
                # Jika target jam ga ketemu tapi data cuma 1, langsung timpa saja
                if 'PLATE' in updates: df.at[0, 'PLATE'] = updates['PLATE']
                if 'DRIVER' in updates: df.at[0, 'DRIVER'] = updates['DRIVER']
                if 'PHONE' in updates: df.at[0, 'PHONE'] = updates['PHONE']
                
    return df

def format_date_custom(date_input):
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
                month_text = None
                for k, v in month_map.items():
                    if k in clean_str:
                        month_text = k
                        break
                if month_text:
                    all_numbers = [(m.start(), int(m.group(0))) for m in re.finditer(r'\b\d{1,2}\b', clean_str)]
                    month_pos = clean_str.find(month_text)
                    if all_numbers and month_pos >= 0:
                        candidates = [num for pos, num in all_numbers if pos < month_pos]
                        if candidates:
                            day = candidates[-1]
                        elif all_numbers:
                            day = all_numbers[0][1]
                else:
                    match_day = re.search(r'\b\d{1,2}\b', clean_str)
                    if match_day: day = int(match_day.group(0))
        if day and month and year:
            day_str = str(day).zfill(2)
            month_str = indo_months.get(month, "")
            if month_str: return f"{day_str} {month_str} {year}"
        return date_str
    except: return str(date_input)

def clean_destination_format(text):
    if pd.isna(text): return ""
    return str(text).upper().strip()

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

def calculate_confidence_score(df):
    scores = []
    for _, row in df.iterrows():
        score = 0.0
        plate_key = 'No. Plat' if 'No. Plat' in df.columns else 'PLATE'
        plate_val = str(row.get(plate_key, '')).strip() if plate_key in df.columns else ""
        if len(plate_val) > 3: score += 0.4

        driver_key = 'Driver' if 'Driver' in df.columns else 'DRIVER'
        driver_val = str(row.get(driver_key, '')).strip() if driver_key in df.columns else ""
        if driver_val and driver_val.lower() != 'nan': score += 0.3

        tujuan_key = 'Tujuan' if 'Tujuan' in df.columns else 'DESTINATION'
        tujuan_val = str(row.get(tujuan_key, '')).strip() if tujuan_key in df.columns else ""
        if tujuan_val and tujuan_val.lower() != 'nan': score += 0.2

        tgl_key = 'Tgl Muat' if 'Tgl Muat' in df.columns else 'DATE'
        tgl_val = str(row.get(tgl_key, '')).strip() if tgl_key in df.columns else ""
        if tgl_val and tgl_val.lower() != 'nan': score += 0.1

        scores.append(round(min(score, 1.0), 3))
    return scores

# =================================================================================
# --- FRONTEND UI: WHITE THEME - PROFESSIONAL EDITION ---
# =================================================================================

st.set_page_config(page_title="Rafay Logistics IDP v2.0", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
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

        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container { padding-top: 2rem !important; max-width: 1400px; }

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
        
        .stTextArea textarea {
            background-color: white !important; color: var(--text-main) !important; border: 1.5px solid var(--border-color) !important;
            border-radius: 6px !important; font-family: 'Courier New', monospace; font-size: 0.85rem; padding: 12px;
        }
        .stTextArea textarea:focus { border-color: var(--accent-color) !important; box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1) !important;}
        
        div.stButton > button {
            background-color: var(--accent-color) !important; color: white !important; border: none !important;
            border-radius: 6px !important; padding: 12px 16px !important; font-weight: 600 !important; width: 100% !important; margin-top: 15px; transition: 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover { background-color: #0D5D56 !important; color: white !important; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }

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

        [data-testid="stDataFrame"] { background-color: white !important; }
        .stDataFrame { background-color: white !important; }
        [data-testid="stDataFrame"] > div { background-color: white !important; }
        [data-testid="stDataFrame"] tbody td { color: var(--text-main) !important; background-color: white !important; border-color: var(--border-color) !important; }
        [data-testid="stDataFrame"] thead th { background-color: #F0F4F4 !important; color: var(--text-main) !important; border-color: var(--border-color) !important; font-weight: 600; }
        [data-testid="stDataFrame"] tbody tr:nth-child(odd) { background-color: white !important; }
        [data-testid="stDataFrame"] tbody tr:nth-child(even) { background-color: #FAFBFC !important; }
        [data-testid="stDataFrame"] table { border-color: var(--border-color) !important; border-collapse: collapse; }
        [data-testid="stDataFrame"] th, [data-testid="stDataFrame"] td { border-color: var(--border-color) !important; padding: 10px 12px; }
        [data-testid="stDataFrame"] tbody tr:hover { background-color: rgba(15, 118, 110, 0.08) !important; }
        
        div.stDownloadButton > button { background-color: var(--success-color) !important; color: white !important; border: none !important; border-radius: 6px !important; font-weight: 600 !important; width: 100% !important; margin-top: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        div.stDownloadButton > button:hover { background-color: #059669 !important; box-shadow: 0 4px 8px rgba(0,0,0,0.15); }

        .result-container { background-color: white; padding: 25px; border-radius: 8px; border: 1.5px solid var(--border-color); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .result-header { color: var(--text-main); font-weight: 700; font-size: 1.1rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }

        .dashboard-container { width: 100%; margin-bottom: 20px; }
        .metric-box { background-color: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .metric-box-label { font-size: 0.75rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .metric-box-value { font-size: 1.75rem; font-weight: 700; color: #1B6987; line-height: 1.2; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_processor(): return ChatBatchProcessor()

def render_top_ui(proses_waktu="--", baris="--", akurasi="--"):
    st.markdown(f"""
        <div class="top-navbar">
            <div class="nav-logo">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-color)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 1 0 0-20z"></path><path d="M12 6v6l4 2"></path></svg>
                <div>
                    <h1 class="nav-title">Rafay Logistics <span class="nav-accent">IDP</span></h1>
                    <p class="nav-subtitle">Intelligent Document Processing v2.0 (IndoBERT + LayoutLMv3)</p>
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
        st.markdown(f"<span style='font-size:0.9rem; color:#666;'>Preview: <code>{preview_format}</code></span>", unsafe_allow_html=True)

        chat_input = st.text_area(
            "Input", height=300, label_visibility="collapsed",
            placeholder="Paste data chat WhatsApp atau dokumen logistik di sini..."
        )

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
                    st.markdown("""<div style='background-color: white; border: 1.5px solid #E1E4E8; border-radius: 8px; padding: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);'><div style='font-size: 1rem; font-weight: 700; color: #1F2937; margin-bottom: 15px;'>Mengekstraksi data dengan AI...</div>""", unsafe_allow_html=True)
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

                    accuracy = calculate_extraction_accuracy(df_raw, df_final)
                    
                    df_office = pd.DataFrame()
                    df_office['No.'] = range(1, len(df_final) + 1)

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

                    confidence_scores = calculate_confidence_score(df_office)
                    avg_confidence = round((sum(confidence_scores) / len(confidence_scores)) * 100, 1) if confidence_scores else 0.0
                    df_office['Confidence'] = confidence_scores

                    end_time = time.time()
                    processing_time = round(end_time - start_time, 2)

                    processing_container.empty()
                    st.session_state['df_office'] = df_office
                    st.session_state.waktu = f"{processing_time}s"
                    st.session_state.baris = f"{len(df_office)} Order"
                    st.session_state.akurasi = f"{accuracy}%"
                    st.session_state.avg_confidence = avg_confidence
                    st.session_state.processing_time = processing_time

                    st.rerun()
                else:
                    processing_container.empty()
                    st.error("Ekstraksi data gagal. Silakan periksa format input dokumen.")
                    
                if os.path.exists(temp_path): os.remove(temp_path)
                    
        if 'df_office' in st.session_state:
            dashboard_col1, dashboard_col2, dashboard_col3 = st.columns(3, gap="medium")
            with dashboard_col1:
                st.markdown(f"""<div class="metric-box"><div class="metric-box-label">Model Confidence</div><div class="metric-box-value">{st.session_state.get('avg_confidence', 0.0)}%</div></div>""", unsafe_allow_html=True)
            with dashboard_col2:
                st.markdown(f"""<div class="metric-box"><div class="metric-box-label">Processing Time</div><div class="metric-box-value">{st.session_state.get('processing_time', 0.0)}s</div></div>""", unsafe_allow_html=True)
            with dashboard_col3:
                st.markdown(f"""<div class="metric-box"><div class="metric-box-label">Total Records</div><div class="metric-box-value">{len(st.session_state['df_office'])}</div></div>""", unsafe_allow_html=True)

            st.divider()
            st.markdown("<div class='result-container'>", unsafe_allow_html=True)
            st.markdown("<div class='result-header'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='3' width='18' height='18' rx='2' ry='2'></rect><line x1='3' y1='9' x2='21' y2='9'></line><line x1='9' y1='21' x2='9' y2='9'></line></svg>Hasil Ekstraksi & Validasi</div>", unsafe_allow_html=True)
            st.dataframe(st.session_state['df_office'], use_container_width=True)
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Jangan sertakan 'Confidence' ke Excel final
                df_export = st.session_state['df_office'].drop(columns=['Confidence'], errors='ignore')
                df_export.to_excel(writer, index=False, sheet_name='Laporan')
                wb = writer.book
                ws = writer.sheets['Laporan']
                h_fmt = wb.add_format({'bold': True, 'bg_color': '#0F766E', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                b_fmt = wb.add_format({'border': 1, 'valign': 'vcenter'})
                for c, val in enumerate(df_export.columns): ws.write(0, c, val, h_fmt)
                ws.set_column('A:A', 5)
                ws.set_column('B:L', 18)
                for r in range(len(df_export)):
                    for c in range(len(df_export.columns)):
                        val = df_export.iloc[r, c]
                        ws.write(r+1, c, "" if pd.isna(val) else val, b_fmt)

            st.download_button(
                label="Download Laporan Excel Rafay",
                data=buffer.getvalue(),
                file_name=f"Rafay_IDP_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
            )
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()