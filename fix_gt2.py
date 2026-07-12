with open('data_uji/ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

bad_block_start = 0
for i in range(len(lines)):
    if '"label": "NO_MATCH"' in lines[i] and '    },' in lines[i+1]:
        bad_block_start = i + 2
        break

good_lines = lines[:bad_block_start]

good_block = '''    {
        "text_a": "[05.31, 7/5/2026] Akbar Rafay: Request Unit On Call Tgl 02 Mei 26\\n\\n3 UNIT CDDL 24 CBM\\nLokasi : JNE SRG\\nWaktu lodng : 07:00 03-05-2026\\nRute/tujuan : SUB-CGK\\nDRVER : Dedi\\nNopol : AB 1448 JJ\\nNo hpp : 08151207919\\n\\nnoted pak, ini data masuk dari lapangan\\nWaktu lodng : 08:00 04-05-2026\\nRute/tujuan : SUB-CGK\\nDRVER :\\nNopol :",
        "text_b": "Request Ulang dan Tambahan Unit On Call Tgl 02 Mei 26\\n\\nPak yang buat rute SUB-CGK jam 8 pagi besok (04-05-2026),\\nsupirnya pakai pak Wahyu aja plat D 1234 ABC hp 08999999.",
        "label": "NO_MATCH"
    }
]'''

good_lines.append(good_block)

with open('data_uji/ground_truth_pencocokan.json', 'w', encoding='utf-8') as f:
    f.writelines(good_lines)

print("Fixed!")
