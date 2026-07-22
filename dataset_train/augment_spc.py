import json
import random
import argparse
import os
import re

MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REPLACEMENT_MONTHS = ["Januari", "Februari", "Maret", "Jan", "Feb", "Mar"]

def augment_spc_pair(text_a, text_b):
    # Gabungkan teks agar penggantian konsisten di text_a dan text_b
    pair_text = text_a + " ||| " + text_b
    
    # 1. Dates (Format kata: 22 MARET 2026)
    date_pattern_word = r'\b\d{1,2}[\s-]+(?:' + '|'.join(MONTHS) + r')[\s-]+\d{2,4}\b'
    dates_found = list(set(re.findall(date_pattern_word, pair_text, flags=re.IGNORECASE)))
    
    # 2. Dates (Format angka: 23-03-2026 atau 23/03/2026)
    date_pattern_digit = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
    dates_digit_found = list(set(re.findall(date_pattern_digit, pair_text)))
    
    date_map = {}
    for d in dates_found:
        new_d = f"{random.randint(1,28):02d} {random.choice(REPLACEMENT_MONTHS).upper()} {random.choice([2025, 2026, 2027])}"
        date_map[d] = new_d
        
    for d in dates_digit_found:
        new_d = f"{random.randint(1,28):02d}-{random.randint(1,3):02d}-{random.choice([2025, 2026, 2027])}"
        date_map[d] = new_d

    # Replace dari yang terpanjang ke terpendek
    date_keys = sorted(date_map.keys(), key=len, reverse=True)
    for old in date_keys:
        new = date_map[old]
        pattern = re.escape(old)
        text_a = re.sub(pattern, new, text_a, flags=re.IGNORECASE)
        text_b = re.sub(pattern, new, text_b, flags=re.IGNORECASE)
        
    # 3. Times
    time_pattern = r'\b\d{2}[:\.]\d{2}\b'
    times_found = list(set(re.findall(time_pattern, pair_text)))
    time_map = {}
    for t in times_found:
        time_map[t] = f"{random.randint(0,23):02d}:00"
        
    for old in sorted(time_map.keys(), key=len, reverse=True):
        new = time_map[old]
        text_a = text_a.replace(old, new)
        text_b = text_b.replace(old, new)
        
    # 4. Nopol
    nopol_pattern = r'\b[A-Z]{1,2} \d{1,4} [A-Z]{1,3}\b'
    nopols_found = list(set(re.findall(nopol_pattern, pair_text)))
    nopol_map = {}
    for n in nopols_found:
        plat = random.choice(['B','D','F','L','W','N','S','BK','BM','BE','AD','AB'])
        num = random.randint(1000, 9999)
        suf = random.choice(['AA','BB','CC','DD','EE','AB','XYZ','U','TX','RX'])
        nopol_map[n] = f"{plat} {num} {suf}"
        
    for old in sorted(nopol_map.keys(), key=len, reverse=True):
        new = nopol_map[old]
        text_a = text_a.replace(old, new)
        text_b = text_b.replace(old, new)
        
    # 5. Phones
    phone_pattern = r'\b08\d{8,11}\b'
    phones_found = list(set(re.findall(phone_pattern, pair_text)))
    phone_map = {}
    for p in phones_found:
        phone_map[p] = f"08{random.randint(100000000, 9999999999)}"
        
    for old in sorted(phone_map.keys(), key=len, reverse=True):
        new = phone_map[old]
        text_a = text_a.replace(old, new)
        text_b = text_b.replace(old, new)
        
    phone_pattern2 = r'\+62 \d{3}-\d{4}-\d{3,4}'
    phones_found2 = list(set(re.findall(phone_pattern2, pair_text)))
    phone_map2 = {}
    for p in phones_found2:
        phone_map2[p] = f"+62 8{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        
    for old in sorted(phone_map2.keys(), key=len, reverse=True):
        new = phone_map2[old]
        text_a = text_a.replace(old, new)
        text_b = text_b.replace(old, new)
        
    return text_a, text_b

def parse_txt_to_spc_data(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Pisahkan berdasarkan REQUEST ORDER
    blocks = re.split(r'\n(?=REQ)', '\n' + content)
    blocks = [b.strip() for b in blocks if b.strip()]
    
    half = len(blocks) // 2
    induk_blocks = blocks[:half]
    susulan_blocks = blocks[half:]
    
    data = []
    for a, b in zip(induk_blocks, susulan_blocks):
        # Ekstrak informasi dari Induk (a) untuk membuat text_a bergaya spc_train.json
        # 1. Tanggal
        date_match = re.search(r'(?i)ON\s*CALL\s+(.*)', a)
        ro_date = date_match.group(1).strip() if date_match else "UNKNOWN DATE"
        
        # 2. Target Qty & Truck
        unit_match = re.search(r'(?i)(\d+)[ \t]+UNIT[ \t]+(.*?)(?=\n|$)', a)
        target_qty = int(unit_match.group(1)) if unit_match else 0
        truck_type = unit_match.group(2).strip() if unit_match else "UNKNOWN TRUCK"
        
        # 3. Pickup
        pickup_match = re.search(r'(?i)Lok.*?:\s*(.*?)(?=\n|$)', a)
        pickup = pickup_match.group(1).strip() if pickup_match else "UNKNOWN LOKASI"
        
        # 4. Route
        route_match = re.search(r'(?i)Rute.*?:\s*(.*?)(?=\n|$)', a)
        route = route_match.group(1).strip() if route_match else "UNKNOWN RUTE"
        
        # 5. Extract existing drivers from Induk
        # Cari blok waktu, nama, nopol, hp
        drivers = []
        driver_blocks = re.findall(r'(?i)(?:Waktu|Jam|lOADING).*?:\s*(.*?)\n.*?(?:NAMA|DRIVER|Driverr).*?:\s*(.*?)\n.*?Nopol.*?:\s*(.*?)\n.*?No\s*(?:HP|tLP|tELPON).*?:\s*(.*?)(?=\n|$)', a)
        for db in driver_blocks:
            waktu, nama, nopol, hp = [x.strip() for x in db]
            drivers.append(f"{waktu} {nama} {nopol} {hp}")
            
        complete = len(drivers)
        empty = target_qty - complete
        existing_drivers_str = " | ".join(drivers) if drivers else "None"
        
        # Use ORDER_STATE format for all
        text_a = f"ORDER_STATE | RO={ro_date}; target={target_qty}; complete={complete}; empty={empty}; truck={truck_type}; pickup={pickup}; route={route}; existing_driver={existing_drivers_str}"
            
        data.append({
            "text_a": text_a,
            "text_b": b.replace('\n', ' '), # text_b in spc_train.json is usually single-line
            "label": "MATCH"
        })
    return data

def generate_spc_dataset(input_file, output_file, target_count):
    if input_file.lower().endswith('.txt'):
        data = parse_txt_to_spc_data(input_file)
    else:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
    print(f"Membaca {len(data)} pasang data asli dari {input_file} sebagai template")
    
    augmented_data = []
    
    # Generate exactly target_count by randomly picking from templates and augmenting
    for i in range(target_count):
        item = random.choice(data)
        text_a = item['text_a']
        text_b = item['text_b']
        
        aug_text_a, aug_text_b = augment_spc_pair(text_a, text_b)
        
        new_item = {
            "pair_id": f"aug_spc_{i+1:05d}",
            "text_a": aug_text_a,
            "text_b": aug_text_b,
            "label": item['label']
        }
        augmented_data.append(new_item)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(augmented_data, f, indent=4)
        
    print(f"Berhasil membuat {target_count} dataset SPC augmentasi di {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Script Procedural Augmentation SPC Dataset (Berbasis Template Input)")
    parser.add_argument('--input', type=str, required=True, help="Path ke file input mentah SPC (.json atau .txt)")
    parser.add_argument('--output', type=str, required=True, help="Path ke file output hasil augmentasi (.json)")
    parser.add_argument('--count', type=int, default=15000, help="Jumlah data yang ingin digenerate (default: 15000)")
    args = parser.parse_args()
    
    print(f"Mulai Augmentasi Procedural SPC...\nInput: {args.input}\nOutput: {args.output}\nTarget: {args.count} data")
    generate_spc_dataset(args.input, args.output, args.count)
