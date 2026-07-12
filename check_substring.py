import json
import re

def clean(t):
    return re.sub(r'\s+', '', str(t)).strip().lower()

with open('data_uji/ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    gt_data = json.load(f)

# Mocking the event generator from positife_combine.txt
with open('data_uji/positife_combine.txt', 'r', encoding='utf-8') as f:
    pos_text = f.read()

# Let's see which MATCH items in GT cannot be found in pos_text
cand_text = clean(pos_text)

failures = []
for i, item in enumerate(gt_data):
    if item['label'] == 'MATCH':
        ta = clean(item['text_a'])
        if ta not in cand_text:
            failures.append((i, item['text_a'][:30]))

print(f"Number of MATCH labels in JSON that fail to substring-match positife_combine.txt: {len(failures)}")
for f in failures:
    print(f)
