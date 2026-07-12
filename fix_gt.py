import re

with open('data_uji/ground_truth_pencocokan.json', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the specific malformed block
bad_block = """    {
        "text_a": "[05.31, 7/5/2026] Akbar Rafay: Request Unit On Call Tgl 02 Mei 26

3 UNIT CDDL 24 CBM
Lokasi : JNE SRG
Waktu lodng : 07:00 03-05-2026
Rute/tujuan : SUB-CGK
DRVER : Dedi
Nopol : AB 1448 JJ
No hpp : 08151207919

noted pak, ini data masuk dari lapangan
Waktu lodng : 08:00 04-05-2026
Rute/tujuan : SUB-CGK
DRVER :
Nopol :",
        "text_b": "Request Ulang dan Tambahan Unit On Call Tgl 02 Mei 26

Pak yang buat rute SUB-CGK jam 8 pagi besok (04-05-2026),
supirnya pakai pak Wahyu aja plat D 1234 ABC hp 08999999.",
        "label": "NO_MATCH"
    }"""

good_block = """    {
        "text_a": "[05.31, 7/5/2026] Akbar Rafay: Request Unit On Call Tgl 02 Mei 26\\n\\n3 UNIT CDDL 24 CBM\\nLokasi : JNE SRG\\nWaktu lodng : 07:00 03-05-2026\\nRute/tujuan : SUB-CGK\\nDRVER : Dedi\\nNopol : AB 1448 JJ\\nNo hpp : 08151207919\\n\\nnoted pak, ini data masuk dari lapangan\\nWaktu lodng : 08:00 04-05-2026\\nRute/tujuan : SUB-CGK\\nDRVER :\\nNopol :",
        "text_b": "Request Ulang dan Tambahan Unit On Call Tgl 02 Mei 26\\n\\nPak yang buat rute SUB-CGK jam 8 pagi besok (04-05-2026),\\nsupirnya pakai pak Wahyu aja plat D 1234 ABC hp 08999999.",
        "label": "NO_MATCH"
    }"""

if bad_block in text:
    text = text.replace(bad_block, good_block)
    with open('data_uji/ground_truth_pencocokan.json', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed!")
else:
    print("Bad block not found.")
