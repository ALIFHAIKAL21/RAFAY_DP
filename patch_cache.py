import re

file_path = 'c:\\Ngoding\\Skripsi\\IDP_RAFAY\\Skripsi_rafay_IDP\\stage2_pair_visual_test.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add st.cache_data to the specific heavy functions
funcs_to_cache = [
    "def stage2_output_events_from_rows(",
    "def stage2_model_error_rows(",
    "def stage2_output_events_with_model_errors("
]

for func in funcs_to_cache:
    if f"@st.cache_data" not in content.split(func)[0][-50:]:
        content = content.replace(func, f"@st.cache_data(show_spinner=False, max_entries=10)\n{func}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully')
