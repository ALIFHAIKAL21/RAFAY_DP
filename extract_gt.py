
import json
import re
import os

files = {
    "positife_combine.txt": "test_case/stres_test/positife_combine.txt",
    "test_case01.txt": "test_case/pesanan_baru/test_case01.txt",
    "test_case_s01.txt": "test_case/pesanan_susulan/test_case_s01.txt",
    "ner_negative.txt": "test_case/negative_test/ekstraksi/ner_negative.txt"
}

def extract_entities(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Regex patterns
    ro_date_pattern = re.compile(r"REQUEST(?:T)?\s*ORDER(?:\s*ULANG)?\s*ONCALL\s*(\d{1,2}\s*[A-Za-z]+\s*\d{2,4})|Request Unit On Call Tgl\s*(\d{1,2}\s*[A-Za-z]+\s*\d{2,4})", re.IGNORECASE)
    plate_pattern = re.compile(r"No(?:pol| pol)\s*:\s*([A-Z]{1,2}\s*\d{1,4}\s*[A-Z]{0,3})", re.IGNORECASE)
    origin_pattern = re.compile(r"Lokasi\s*:\s*(.+)", re.IGNORECASE)
    dest_pattern = re.compile(r"Rute/(?:tujuan|tujan|tuj)\s*:\s*(.+)", re.IGNORECASE)
    unit_type_pattern = re.compile(r"\d+\s*UNIT\s*([A-Z0-9\s]+)", re.IGNORECASE)

    ro_dates = []
    for match in ro_date_pattern.finditer(text):
        ro_dates.append(match.group(1) or match.group(2))

    plates = []
    for match in plate_pattern.finditer(text):
        if match.group(1).strip().lower() not in ["", "menyusul", "belum ada"]:
            plates.append(match.group(1).strip())

    origins = []
    for match in origin_pattern.finditer(text):
        if match.group(1).strip():
            origins.append(match.group(1).strip())

    dests = []
    for match in dest_pattern.finditer(text):
        if match.group(1).strip():
            dests.append(match.group(1).strip())
            
    unit_types = []
    for match in unit_type_pattern.finditer(text):
        if match.group(1).strip():
            unit_types.append(match.group(1).strip())

    # De-duplicate while preserving order
    return {
        "RO_DATE": list(dict.fromkeys(ro_dates)),
        "PLATE": list(dict.fromkeys(plates)),
        "ORIGIN": list(dict.fromkeys(origins)),
        "DESTINATION": list(dict.fromkeys(dests)),
        "UNIT_TYPE": list(dict.fromkeys(unit_types))
    }

master_gt = {}
for name, path in files.items():
    if os.path.exists(path):
        master_gt[name] = extract_entities(path)
    else:
        print(f"File not found: {path}")

# Write to JSON
out_path = "test_case/negative_test/GT_NER.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(master_gt, f, indent=4)

print(f"GT saved to {out_path}")
