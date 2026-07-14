import json

# Read GT_NER.json
with open('data_uji/GT_NER.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update UNIT_QTY for data_uji_demo.txt
if 'data_uji_demo.txt' in data:
    data['data_uji_demo.txt']['UNIT_QTY'] = [str(i) for i in range(7, 25)]

# Write back GT_NER.json
with open('data_uji/GT_NER.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print("Updated GT_NER.json with unique quantities.")
