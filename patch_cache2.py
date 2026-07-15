import re

file_path = 'c:\\Ngoding\\Skripsi\\IDP_RAFAY\\Skripsi_rafay_IDP\\stage2_pair_visual_test.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

funcs_to_cache = [
    "def stage2_match_official_metrics("
]

for func in funcs_to_cache:
    if f"@st.cache_data" not in content.split(func)[0][-50:]:
        content = content.replace(func, f"@st.cache_data(show_spinner=False, max_entries=10)\n{func}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully')
