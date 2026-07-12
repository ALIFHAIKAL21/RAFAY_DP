import json
import re

with open('data_uji/ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    gt_data = json.load(f)

with open('data_uji/positife_combine.txt', 'r', encoding='utf-8') as f:
    pos_data = f.read()

# For each MATCH in gt_data, check if text_a is exactly in pos_data
not_found = []
for i, item in enumerate(gt_data):
    if item['label'] == 'MATCH':
        # Clean whitespaces for robust check
        clean_text_a = re.sub(r'\s+', '', item['text_a']).lower()
        clean_pos_data = re.sub(r'\s+', '', pos_data).lower()
        if clean_text_a not in clean_pos_data:
            not_found.append(i)

print(f"MATCH entries not perfectly in positife_combine.txt: {not_found}")
