import pandas as pd
import re
from io import BytesIO
from datetime import datetime

DRIVER_BLACKLIST = ["RAFAY","AKBAR","ADMIN","JNE","LOGISTIK","EXPEDISI","PENGIRIM","ONCALL","REQUEST"]

def auto_format_chat_input(text):
    if not text: return ""
    wa_pattern = r"(?=\[\d{2}[.,:]\d{2}[, ]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:]+:)"
    chunks = re.split(wa_pattern, text)
    valid_text = ""
    for chunk in chunks:
        if not chunk.strip(): continue
        chunk_lower = chunk.lower()
        if "contoh chat" in chunk_lower or "latih ai" in chunk_lower or "minta contoh" in chunk_lower: continue
        valid_text += chunk
    if not valid_text.strip(): valid_text = text 
    lines = valid_text.split('\n')
    formatted_lines = []
    pattern = r"(?i)(Waktu loading\s*:\s*)(.*?)(\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}|\s+\d{1,2}\s+[a-zA-Z]+\s+\d{4})"
    
    # FIX: State-based tracking untuk [HH.MM, DD/MM/YYYY] header timestamp
    current_header_date = None
    
    for line in lines:
        # Deteksi header timestamp [HH.MM, DD/MM/YYYY] dan simpan sebagai state
        header_timestamp_pattern = r'\[(\d{2}[.,:]\d{2})\s*,\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]'
        timestamp_match = re.search(header_timestamp_pattern, line)
        if timestamp_match:
            current_header_date = timestamp_match.group(2)
            formatted_lines.append(line)
            continue
        
        match = re.search(pattern, line)
        if match:
            prefix = match.group(1); jam = match.group(2).strip(); tgl = match.group(3).strip() 
            formatted_lines.append(f"\nREQUEST ORDER KHUSUS {tgl}")
            formatted_lines.append(f"{prefix}{jam}")
            current_header_date = tgl  # Update state dengan tanggal dari pattern match
        else:
            formatted_lines.append(line)
    return "\n".join(formatted_lines)

def extract_plate_aggressive(text):
    if pd.isna(text): return ""
    match = re.search(r"\b([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{1,3})\b", str(text).upper())
    return match.group(1) if match else ""

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
    if not name or pd.isna(name) or str(name).lower() == 'none': return ""
    clean_name = str(name).strip().title()
    for bad_word in DRIVER_BLACKLIST:
        if bad_word.lower() in clean_name.lower(): return ""
    return clean_name

def sanitize_row_data(row):
    d = str(row.get('DATE', '')).strip(); t = str(row.get('TIME', '')).strip()
    orig_text = str(row.get('Original_Text', '')).strip(); drv = str(row.get('DRIVER', '')).strip()
    if d.lower() in ['none', 'nan', 'nat']: d = ""
    if t.lower() in ['none', 'nan', 'nat']: t = ""
    
    has_segera = False
    if "segera" in t.lower(): has_segera = True
    elif "segera" in d.lower(): has_segera = True; d = "" 
    elif "segera" in drv.lower(): has_segera = True 
    elif "segera" in orig_text.lower(): has_segera = True 
    if has_segera: t = "SEGERA"
        
    is_time_misplaced = re.match(r'^(\d{1,2}|\d{1,2}[:.]\d{2})$', d)
    if is_time_misplaced:
        if not t or t == "SEGERA": 
             if t != "SEGERA": t = d
        d = ""
        
    if t and t != "SEGERA":
        t = t.replace(".", ":").replace("*", "")
        if re.match(r'^\d{1,2}$', t): t = f"{t.zfill(2)}:00"
    
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

    row['DATE'] = d; row['TIME'] = t
    return row

def repair_headers(df):
    if df is None or df.empty: return df
    for col in ['DESTINATION', 'ORIGIN', 'UNIT_TYPE']: df[col] = df[col].replace(['', 'None', 'NONE', 'nan', 'nan '], pd.NA)
    for i in range(len(df)):
        qty_val = str(df.at[i, 'UNIT_QTY'])
        if any(char.isdigit() for char in qty_val):
            for lookahead in range(1, 4):
                if i + lookahead < len(df):
                    for c in ['DESTINATION', 'ORIGIN', 'UNIT_TYPE']:
                        if pd.isna(df.at[i, c]): df.at[i, c] = df.at[i + lookahead, c]
    return df

def mark_order_block(df):
    df = df.copy(); df['BLOCK_ID'] = 0; current_block = 0
    for i in range(len(df)):
        qty_raw = str(df.at[i, 'UNIT_QTY']); is_header = False
        try:
            q_num = int(''.join(filter(str.isdigit, qty_raw))) if any(char.isdigit() for char in qty_raw) else 0
            if q_num > 1 or (q_num == 1 and pd.notna(df.at[i, 'UNIT_TYPE'])): is_header = True
        except: pass
        if is_header: current_block += 1
        df.at[i, 'BLOCK_ID'] = current_block
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
            try:
                if int(''.join(filter(str.isdigit, str(row.get('UNIT_QTY', ''))))) > 1: header_row = row; continue
            except: pass
            if header_row is None and 'UNIT_QTY' in row and str(row['UNIT_QTY']).strip() == '1' and pd.notna(row.get('UNIT_TYPE')):
                header_row = row; continue

            row = sanitize_row_data(row)
            d_name = clean_driver_name(row.get('DRIVER', ''))
            t_val = str(row.get('TIME', '')).lower()
            has_time = pd.notna(row.get('TIME')) and (any(c.isdigit() for c in t_val) or "segera" in t_val)
            
            if not str(row.get('PLATE', '')) or str(row.get('PLATE', '')).lower() == 'nan':
                found_plate = extract_plate_aggressive(str(row.get('Original_Text', '')) + " " + str(row.get('DRIVER', '')))
                if found_plate: row['PLATE'] = found_plate
            
            has_plate = pd.notna(row.get('PLATE')) and len(str(row.get('PLATE'))) > 3
            if d_name or has_time or has_plate:
                row['DRIVER'] = d_name; valid_candidates.append(row)
        
        if header_row is None and len(block_data) > 0: header_row = block_data.iloc[0]

        for i in range(target_qty):
            if i < len(valid_candidates):
                candidate = valid_candidates[i]
                for col in ['ORIGIN', 'DESTINATION', 'UNIT_TYPE', 'DATE']:
                    if pd.isna(candidate.get(col)) or str(candidate.get(col)).strip() == "":
                        h_val = header_row.get(col)
                        if col == 'DATE' and h_val and re.search(r'\d', str(h_val)): candidate[col] = h_val
                        elif col != 'DATE': candidate[col] = h_val
                final_rows.append(candidate)
            else:
                clean_slot = header_row.copy()
                clean_slot['DRIVER'] = ""; clean_slot['PLATE'] = ""; clean_slot['PHONE'] = ""; clean_slot['TIME'] = ""; clean_slot['UNIT_QTY'] = 1
                clean_slot['DATE'] = header_row['DATE'] if header_row.get('DATE') and re.search(r'\d', str(header_row.get('DATE'))) else ""
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

        # Ekstrak target time dalam format HH:MM atau HH.MM
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

    # Terapkan updates ke row yang TIME-nya matching
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
    try:
        if pd.isna(date_input) or str(date_input).strip() == "": return ""
        date_str = re.sub(r'[^\w\s/\-]', '', str(date_input).strip())
        indo_months = {1:'JANUARI',2:'FEBRUARI',3:'MARET',4:'APRIL',5:'MEI',6:'JUNI',7:'JULI',8:'AGUSTUS',9:'SEPTEMBER',10:'OKTOBER',11:'NOVEMBER',12:'DESEMBER'}
        day, month, year = None, None, None
        match_digit = re.search(r'(\d{1,2})[/\-\s]+(\d{1,2})[/\-\s]+(\d{4})', date_str)
        if match_digit:
            day, month, year = int(match_digit.group(1)), int(match_digit.group(2)), int(match_digit.group(3))
        else:
            month_map = {'jan':1,'feb':2,'peb':2,'mar':3,'apr':4,'mei':5,'may':5,'jun':6,'jul':7,'agu':8,'aug':8,'sep':9,'okt':10,'oct':10,'nov':11,'des':12,'dec':12}
            clean_str = date_str.lower()
            for k, v in month_map.items():
                if k in clean_str: month = v; break
            if month:
                match_year = re.search(r'\d{4}', clean_str); year = int(match_year.group(0)) if match_year else None
                match_day = re.search(r'\b\d{1,2}\b', clean_str); day = int(match_day.group(0)) if match_day else None
        if day and month and year: return f"{str(day).zfill(2)} {indo_months.get(month, '')} {year}"
        return date_str
    except: return str(date_input)

def clean_destination_format(text):
    return re.sub(r'\s*-\s*', ',', str(text).upper().strip()) if pd.notna(text) else ""

def generate_office_report(df_raw):
    """Fungsi utama untuk mengubah raw DataFrame dari AI menjadi DataFrame siap pakai ke Office."""
    df_proc = repair_headers(df_raw)
    df_proc = mark_order_block(df_proc)
    
    # Proteksi: pastikan semua kolom yang diperlukan ada sebelum groupby + ffill
    required_cols = ['UNIT_TYPE', 'ORIGIN', 'DESTINATION', 'DATE']
    for col in required_cols:
        if col not in df_proc.columns:
            df_proc[col] = None
    
    # Forward-fill context per blok
    for col in required_cols:
        df_proc[col] = df_proc.groupby('BLOCK_ID')[col].ffill()
    
    df_final = enforce_block_quota(df_proc)
    df_final = apply_revision_logic(df_final)
    
    df_office = pd.DataFrame()
    df_office['No.'] = range(1, len(df_final) + 1)
    df_office['Job Number'] = [f"{42+i:03d}/JNE-RAFAY/II/2026" for i in range(len(df_final))]
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
    
    return df_office

def get_excel_bytes(df_office):
    """Menyulap DataFrame menjadi file Excel siap unduh."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_office.to_excel(writer, index=False, sheet_name='Laporan')
        wb = writer.book; ws = writer.sheets['Laporan']
        h_fmt = wb.add_format({'bold':True, 'bg_color':'#F4B084', 'border':1, 'align':'center'})
        b_fmt = wb.add_format({'border':1, 'valign':'vcenter'})
        for c, val in enumerate(df_office.columns): ws.write(0, c, val, h_fmt)
        ws.set_column('A:A', 5); ws.set_column('B:K', 18)
        for r in range(len(df_office)):
            for c in range(len(df_office.columns)):
                val = df_office.iloc[r,c]
                ws.write(r+1, c, "" if pd.isna(val) else val, b_fmt)
    return buffer.getvalue()