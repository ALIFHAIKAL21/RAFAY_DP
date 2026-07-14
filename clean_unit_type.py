import json
import re

with open('data_uji/GT_NER.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for key in data:
    if 'UNIT_TYPE' in data[key]:
        new_unit_types = []
        for ut in data[key]['UNIT_TYPE']:
            # Take just the alphabetical prefix
            m = re.match(r'([A-Za-z]+)', ut)
            if m:
                new_unit_types.append(m.group(1))
            else:
                new_unit_types.append(ut)
        data[key]['UNIT_TYPE'] = new_unit_types

with open('data_uji/GT_NER.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
print("UNIT_TYPE updated.")
