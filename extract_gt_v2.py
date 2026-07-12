
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

    gt = {
        "UNIT_QTY": [],
        "RO_DATE": [],
        "LOAD_DATE": [],
        "ORIGIN": [],
        "DESTINATION": [],
        "PLATE": [],
        "UNIT_TYPE": [],
        "DRIVER": [],
        "PHONE": []
    }

    # If negative test case, we only allow RO_DATE to be extracted (because the rest is empty/unclear by design)
    is_negative = "ner_negative.txt" in filepath

    for match in re.finditer(r"(\d+)\s*UNIT", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val: gt["UNIT_QTY"].append(val)

    for match in re.finditer(r"(?:REQUEST(?:T)?\s*ORDER(?: ULANG)?\s*ONCALL\s*|Request Unit On Call Tgl\s*)([0-9]{1,2}\s*[A-Za-z]+\s*[0-9]{2,4})", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val: gt["RO_DATE"].append(val)

    for match in re.finditer(r"Waktu\s*load(?:ing|ng|in|i|n)?\s*:\s*([A-Za-z0-9\:\/\-\s]+)", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val and not val.lower().startswith("segera"):
            # Clean up trailing garbage if any
            val = val.split("\n")[0].strip()
            # If negative test and value is junk like "012831414049124" or empty, skip
            if len(val) > 2:
                gt["LOAD_DATE"].append(val)
        elif val.lower().startswith("segera"):
            gt["LOAD_DATE"].append("SEGERA")

    for match in re.finditer(r"Lokasi\s*:\s*([^\n]+)", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val: gt["ORIGIN"].append(val)

    for match in re.finditer(r"Rute/(?:tujuan|tujan|tuj)\s*:\s*([^\n]+)", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val: gt["DESTINATION"].append(val)

    for match in re.finditer(r"(?:No[ \t]*pol|Nopol|NO POL)[ \t]*:[ \t]*([A-Z]{1,2}[ \t]*\d{1,4}[ \t]*[A-Z]{0,3})", text, re.IGNORECASE):
        val = match.group(1).strip()
        # Exclude "menyusul", "belum", etc
        if val and not any(junk in val.lower() for junk in ["menyusul", "belum"]):
            gt["PLATE"].append(val)

    for match in re.finditer(r"\d+[ \t]*UNIT[ \t]+([A-Z0-9 \t\/]+?)(?=\n|$)", text, re.IGNORECASE):
        val = match.group(1).strip()
        # Clean up capacity info
        val = re.sub(r'[\/0-9]+[ \t]*(?:cbm|kubik|ton)?', '', val, flags=re.IGNORECASE).strip()
        if val: gt["UNIT_TYPE"].append(val)

    for match in re.finditer(r"(?:Driver|NAMA|DRVER|DRIVERR)[ \t]*:[ \t]*([A-Za-z \.]+?)(?=\n|$)", text, re.IGNORECASE):
        val = match.group(1).strip()
        # Exclude "masih dicari"
        if val and "dicari" not in val.lower() and "belum" not in val.lower():
            gt["DRIVER"].append(val)

    for match in re.finditer(r"No[ \t]*(?:hp|hpp)[ \t]*:[ \t]*([\+\d\-\s]+)", text, re.IGNORECASE):
        val = match.group(1).strip()
        if val: gt["PHONE"].append(val)

    # De-duplicate
    for k in gt:
        gt[k] = list(dict.fromkeys(gt[k]))
        if is_negative and k != "RO_DATE":
            gt[k] = [] # Blank out negative test

    return gt

if __name__ == "__main__":
    master_gt = {}
    for name, path in files.items():
        if os.path.exists(path):
            master_gt[name] = extract_entities(path)
        else:
            print(f"File not found: {path}")

    # Write to JSON
    out_path = "data_uji/GT_NER.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(master_gt, f, indent=4)

    print(f"GT saved to {out_path}")
