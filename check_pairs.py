import json

with open('c:\\Ngoding\\Skripsi\\IDP_RAFAY\\Skripsi_rafay_IDP\\data_uji_demo\\ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

match_a = set()
match_b = set()
nomatch_a = set()
nomatch_b = set()

for idx, item in enumerate(data):
    if item['label'] == 'MATCH':
        match_a.add(item['text_a'].strip())
        match_b.add(item['text_b'].strip())
    else:
        nomatch_a.add(item['text_a'].strip())
        nomatch_b.add(item['text_b'].strip())

print('Induk (text_a) in NO_MATCH but not in MATCH:')
for a in nomatch_a:
    if a not in match_a:
        print('-', a.split('\\n')[0])

print('\nSusulan (text_b) in NO_MATCH but not in MATCH:')
for b in nomatch_b:
    if b not in match_b:
        print('-', b.split('\\n')[0])
