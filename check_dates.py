import json
import re

with open('data_uji/ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, item in enumerate(data):
    if item['label'] == 'NO_MATCH':
        date_a = re.search(r'(?:ONCALL\s*|Tgl\s*)([0-9]{1,2}\s*[A-Za-z]+\s*[0-9]{2,4})', item['text_a'], re.IGNORECASE)
        date_b = re.search(r'(?:ONCALL\s*|Tgl\s*)([0-9]{1,2}\s*[A-Za-z]+\s*[0-9]{2,4})', item['text_b'], re.IGNORECASE)
        if date_a and date_b:
            print(f"[{i}] {date_a.group(1)} vs {date_b.group(1)}")
