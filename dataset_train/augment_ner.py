import json
import random
import re
import os
import argparse

def generate_procedural_dataset(input_file, output_file, target_count=1000):
    # Baca file mentah sebagai template
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pisahkan setiap order dengan mendeteksi kata kunci REQUEST / REQEST / REQUER / Request
    # Pertama, split berdasarkan newline dan cari baris awal
    lines = content.split('\n')
    templates = []
    current_chunk = []
    
    for line in lines:
        upper_line = line.upper()
        if "REQUEST" in upper_line or "REQUER" in upper_line or "REQEST" in upper_line or "Request" in line:
            if current_chunk:
                chunk_text = "\n".join(current_chunk).strip()
                if len(chunk_text) > 30: # pastikan valid
                    templates.append(chunk_text)
            # bersihkan prefix chat WA jika ada
            clean_line = re.sub(r'^\[.*?\] .*?: ', '', line)
            clean_line = re.sub(r'^.*?Rafay: ', '', clean_line)
            current_chunk = [clean_line]
        else:
            if current_chunk:
                current_chunk.append(line)
                
    if current_chunk:
        chunk_text = "\n".join(current_chunk).strip()
        if len(chunk_text) > 30:
            templates.append(chunk_text)
            
    if not templates:
        print("Tidak ada template ditemukan!")
        return

    print(f"Ditemukan {len(templates)} template dasar dari file {input_file}")

    # Fungsi augmentasi prosedural
    MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    REPLACEMENT_MONTHS = ["Januari", "Februari", "Maret", "Jan", "Feb", "Mar"]
    
    def augment_text(text):
        # 1. Random Date (misal 14 APRIL 2026 -> 05 MEI 2027)
        date_pattern = r'\b\d{1,2}[\s-]+(?:' + '|'.join(MONTHS) + r')[\s-]+\d{2,4}\b'
        def repl_date(m):
            return f"{random.randint(1,28):02d} {random.choice(REPLACEMENT_MONTHS).upper()} {random.choice([2025, 2026, 2027])}"
        text = re.sub(date_pattern, repl_date, text, flags=re.IGNORECASE)
        
        # 2. Random Time (misal 09:00 -> 14:00)
        time_pattern = r'\b\d{2}:\d{2}\b'
        def repl_time(m):
            return f"{random.randint(0,23):02d}:00"
        text = re.sub(time_pattern, repl_time, text)
        
        # 3. Random Nopol (misal B 1234 CD -> F 9999 XX)
        nopol_pattern = r'\b[A-Z]{1,2} \d{1,4} [A-Z]{1,3}\b'
        def repl_nopol(m):
            plat = random.choice(['B','D','F','L','W','N','S','BK','BM','BE','AD','AB'])
            num = random.randint(1000, 9999)
            suf = random.choice(['AA','BB','CC','DD','EE','AB','XYZ','U','TX','RX'])
            return f"{plat} {num} {suf}"
        text = re.sub(nopol_pattern, repl_nopol, text)
        
        # 4. Random Phone (misal 08123456789 -> 08199999999)
        phone_pattern = r'\b08\d{8,11}\b'
        def repl_phone(m):
            return f"08{random.randint(100000000, 9999999999)}"
        text = re.sub(phone_pattern, repl_phone, text)
        
        phone_pattern2 = r'\+62 \d{3}-\d{4}-\d{3,4}'
        def repl_phone2(m):
            return f"+62 8{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        text = re.sub(phone_pattern2, repl_phone2, text)
        
        # 5. Random QTY unit (misal 5 UNIT -> 7 UNIT)
        qty_pattern = r'\b\d{1,2}(?=\s+UNIT)'
        def repl_qty(m):
            return str(random.randint(1, 15))
        text = re.sub(qty_pattern, repl_qty, text, flags=re.IGNORECASE)
        
        return text

    augmented_dataset = []
    
    # Generate exactly target_count
    for i in range(target_count):
        base_template = random.choice(templates)
        augmented = augment_text(base_template)
        
        # Format sesuai dengan raw.json 100% persis
        item = {
            "id": 5001 + i, # Mulai dari 5001 agar mirip raw.json
            "data": {
                "text": augmented
            }
        }
        augmented_dataset.append(item)
        
    # Tulis hasil ke file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(augmented_dataset, f, indent=4)
        
    print(f"Berhasil membuat {target_count} dataset augmentasi di {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script Procedural Augmentation NER Dataset")
    parser.add_argument('--input', type=str, required=True, help="Path ke file input mentah")
    parser.add_argument('--output', type=str, required=True, help="Path ke file output hasil augmentasi (.json)")
    parser.add_argument('--count', type=int, default=1000, help="Jumlah dataset yang ingin digenerate (default: 1000)")
    args = parser.parse_args()
    
    print(f"Mulai Augmentasi Procedural...\nInput: {args.input}\nOutput: {args.output}\nTarget: {args.count} data")
    generate_procedural_dataset(args.input, args.output, args.count)
