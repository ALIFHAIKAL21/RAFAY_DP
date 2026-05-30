import json
import re
import sys
from pathlib import Path

# SETUP PATH IMPORT ---
# Agar bisa membaca src.config dari dalam folder data_processing
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config import AUTO_LABEL_INPUT_FILE, AUTO_LABEL_OUTPUT_FILE

# KONFIGURASI FILE ---
# Default path mengikuti struktur baru `data/chat/raw/*_NER*.json`
# Bisa dioverride via env:
# - AUTO_LABEL_INPUT_PATH
# - AUTO_LABEL_OUTPUT_PATH
INPUT_FILE = AUTO_LABEL_INPUT_FILE
OUTPUT_FILE = AUTO_LABEL_OUTPUT_FILE

def find_offsets(text, pattern, group_index=0):
    """Mencari posisi start dan end dengan dukungan group regex"""
    matches = []
    try:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            try:
                target_text = match.group(group_index)
                start = match.start(group_index)
                end = match.end(group_index)
            except IndexError:
                target_text = match.group(0)
                start = match.start(0)
                end = match.end(0)
                
            if target_text and target_text.strip():
                matches.append({
                    "start": start,
                    "end": end,
                    "text": target_text,
                })
    except Exception as e:
        print(f"Regex Error: {e}")
    return matches

def create_result(start, end, text, label_name, type="labels"):
    res = {
        "from_name": "label",
        "to_name": "text",
        "type": type,
        "value": {
            "start": start,
            "end": end,
            "text": text
        }
    }
    if type == "labels":
        res["value"]["labels"] = [label_name]
    elif type == "choices":
        res["from_name"] = "intent"
        res["value"]["choices"] = [label_name]
    return res

def process_data(data):
    processed_tasks = []
    
    for task in data:
        # Handle format data jika 'data' wrapper tidak ada
        if 'data' in task:
            text = task['data']['text']
        else:
            text = task['text'] # Fallback
            task = {'data': {'text': text}} # Re-structure 

        results = []

        #TEBAK INTENT (KLASIFIKASI) 
        if re.search(r'(CANCEL|BATAL|GAGAL|TIDAK JADI)', text, re.IGNORECASE):
            results.append(create_result(0, 0, "", "CANCEL", type="choices"))
        elif re.search(r'(UPDATE|GANTI|REVISI|UBAH)', text, re.IGNORECASE):
            results.append(create_result(0, 0, "", "UPDATE", type="choices"))
        elif re.search(r'(INFO)', text, re.IGNORECASE):
             results.append(create_result(0, 0, "", "INFO", type="choices"))
        else:
            results.append(create_result(0, 0, "", "NEW_ORDER", type="choices"))

        # TEBAK ENTITAS (LOGIKA PINTAR) 

        # A. TANGGAL (DATE)
        date_patterns = [
            r'(\d{1,2}\s+(?:JANUARI|FEBRUARI|MARET|APRIL|MEI|JUNI|JULI|AGUSTUS|SEPTEMBER|OKTOBER|NOVEMBER|DESEMBER)\s+\d{4})', 
            r'(\d{1,2}\s*-\s*(?:Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s*-\s*\d{4})', 
            r'(\d{1,2}/\d{1,2}/\d{4})' 
        ]
        for dp in date_patterns:
            for m in find_offsets(text, dp, group_index=1):
                results.append(create_result(m['start'], m['end'], m['text'], "DATE"))

        # B. JUMLAH & TIPE UNIT
        unit_match = re.search(r'(\d+)\s+UNIT\s+([A-Za-z0-9\s]+?)(?=\n|Lokasi|$)', text, re.IGNORECASE)
        if unit_match:
            results.append(create_result(unit_match.start(1), unit_match.end(1), unit_match.group(1), "UNIT_QTY"))
            results.append(create_result(unit_match.start(2), unit_match.end(2), unit_match.group(2).strip(), "UNIT_TYPE"))

        # C. WAKTU LOADING (TIME)
        time_patterns = [
            # Pattern 1: "Waktu loading : [TIME]" atau "Waktu loading: [TIME]" (dengan atau tanpa spasi)
            r'Waktu\s+loading\s*:\s*(SEGERA|ASAP|UNKNOWN|\d{1,2}:\d{2})',

            # Pattern 2: "Waktu loading : [TIME] [TANGGAL]" - extract hanya TIME bagian
            r'Waktu\s+loading\s*:\s*(\d{1,2}:\d{2}|\d{1,2})\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'Waktu\s+loading\s*:\s*(\d{1,2}:\d{2}|\d{1,2})\s+\d{1,2}\s+(?:JANUARI|FEBRUARI|MARET|APRIL|MEI|JUNI|JULI|AGUSTUS|SEPTEMBER|OKTOBER|NOVEMBER|DESEMBER)',

            # Pattern 3: "Waktu loading : SEGERA [TANGGAL]"
            r'Waktu\s+loading\s*:\s*(SEGERA|ASAP)\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}',
            r'Waktu\s+loading\s*:\s*(SEGERA|ASAP)\s+\d{1,2}\s+(?:JANUARI|FEBRUARI|MARET|APRIL|MEI|JUNI|JULI|AGUSTUS|SEPTEMBER|OKTOBER|NOVEMBER|DESEMBER)',

            # Pattern 4: "jam [TIME]" atau "pukul [TIME]"
            r'(?:jam|pukul)\s+(\d{1,2}:\d{2}|SEGERA|ASAP)',

            # Pattern 5: "Loading jam [TIME]" atau "Loading pukul [TIME]"
            r'[Ll]oading\s+(?:jam|pukul)\s+(\d{1,2}:\d{2})',

            # Pattern 6: Format informal "loading [TIME]" tanpa "jam"
            r'[Ll]oading\s+(\d{1,2}:\d{2})(?:\s|$|\n)',

            # Pattern 7: "Jam loading [TIME]"
            r'Jam\s+loading\s*[:\s]+(\d{1,2}:\d{2}|SEGERA|ASAP)'
        ]
        for tp in time_patterns:
            for m in find_offsets(text, tp, group_index=1):
                 # Normalize single digit jam menjadi HH:00
                 time_val = m['text']
                 if re.match(r'^\d{1,2}$', time_val):  # Hanya digit tanpa :MM
                     time_val = f"{time_val.zfill(2)}:00"
                 results.append(create_result(m['start'], m['end'], time_val, "TIME"))

        # D. LOKASI ASAL (ORIGIN)
        origin_match = re.search(r'Lokasi\s*:\s*(.*)', text, re.IGNORECASE)
        if origin_match:
            raw_origin = origin_match.group(1).strip()
            if "+" in raw_origin:
                sub_origins = find_offsets(text, r'([A-Z0-9\s]+)(?:\+|$)', group_index=1)
                for so in sub_origins:
                    if so['start'] >= origin_match.start(1) and so['end'] <= origin_match.end(1):
                         results.append(create_result(so['start'], so['end'], so['text'].strip(), "ORIGIN"))
            else:
                results.append(create_result(origin_match.start(1), origin_match.end(1), raw_origin, "ORIGIN"))

        # E. TUJUAN (DESTINATION)
        dest_match = re.search(r'Rute/tujuan\s*:\s*(.*)', text, re.IGNORECASE)
        if dest_match:
            full_dest_line = dest_match.group(1)
            start_offset = dest_match.start(1)
            
            if " - " in full_dest_line:
                parts = full_dest_line.split(" - ")
                target_part = parts[-1] 
                local_start = full_dest_line.find(target_part)
                global_start = start_offset + local_start
                
                if "," in target_part:
                    sub_dests = re.finditer(r'([^,]+)', target_part)
                    for sd in sub_dests:
                        s_text = sd.group(1).strip()
                        s_start = global_start + sd.start(1)
                        if s_text:
                            results.append(create_result(s_start, s_start + len(s_text), s_text, "DESTINATION"))
                else:
                    results.append(create_result(global_start, global_start + len(target_part.strip()), target_part.strip(), "DESTINATION"))
            else:
                if "," in full_dest_line:
                      sub_dests = re.finditer(r'([^,]+)', full_dest_line)
                      for sd in sub_dests:
                        s_text = sd.group(1).strip()
                        if s_text: 
                            s_start = start_offset + sd.start(1)
                            if sd.group(1).startswith(" "): s_start += 1
                            results.append(create_result(s_start, s_start + len(s_text), s_text, "DESTINATION"))
                else:
                    results.append(create_result(start_offset, start_offset + len(full_dest_line.strip()), full_dest_line.strip(), "DESTINATION"))

        # F. DRIVER
        driver_match = re.search(r'driver\s*:\s*(.*)', text, re.IGNORECASE)
        if driver_match:
            results.append(create_result(driver_match.start(1), driver_match.end(1), driver_match.group(1).strip(), "DRIVER"))

        # G. PLAT NOMOR 
        nopol_line_match = re.search(r'Nopol\s*:\s*(.*)', text, re.IGNORECASE)
        if nopol_line_match:
            raw_plate = nopol_line_match.group(1)
            plate_regex = r'([A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{0,3})' 
            pm = re.search(plate_regex, raw_plate)
            if pm:
                real_start = nopol_line_match.start(1) + pm.start(1)
                real_end = nopol_line_match.start(1) + pm.end(1)
                results.append(create_result(real_start, real_end, pm.group(1), "PLATE"))

        # H. NO HP 
        phone_match = re.search(r'(08\d{8,13})', text)
        if phone_match:
            results.append(create_result(phone_match.start(1), phone_match.end(1), phone_match.group(1), "PHONE"))
            
        # I. REASON
        if "CANCEL" in text or "BATAL" in text:
             reason_match = re.search(r'(?:karena|masalah|unit)\s+(.*)', text, re.IGNORECASE)
             if reason_match:
                 results.append(create_result(reason_match.start(0), reason_match.end(0), reason_match.group(0), "REASON"))


        # GABUNGKAN HASIL 
        task['predictions'] = [{
            "model_version": "v2_advanced_logic",
            "score": 0.95,
            "result": results
        }]
        processed_tasks.append(task)

    return processed_tasks

def main():
    print("🤖 Memulai Auto-Labeling...")
    print(f"📂 Input: {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ ERROR: File '{INPUT_FILE}' tidak ditemukan.")
        print("👉 Pastikan file JSON mentah sudah ada di folder 'data/chat/raw/'")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        final_data = process_data(raw_data)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ SUKSES! {len(final_data)} data diproses.")
        print(f"📂 Output tersimpan di: {OUTPUT_FILE}")
        print("👉 Silakan import file output ini ke Label Studio!")

    except json.JSONDecodeError:
        print(f"❌ ERROR: Format JSON Input rusak/tidak valid.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()
