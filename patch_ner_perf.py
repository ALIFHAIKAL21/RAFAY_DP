import re

file_path = 'c:\\Ngoding\\Skripsi\\IDP_RAFAY\\Skripsi_rafay_IDP\\stage2_pair_visual_test.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add st.cache_data to build_simple_ner_eval_cards
content = content.replace(
    "def build_simple_ner_eval_cards(",
    "@st.cache_data(show_spinner=False, max_entries=10)\ndef build_simple_ner_eval_cards("
)

# Add st.cache_data to build_ner_stage2_card_groups
content = content.replace(
    "def build_ner_stage2_card_groups(",
    "@st.cache_data(show_spinner=False, max_entries=10)\ndef build_ner_stage2_card_groups("
)

# Add st_fragment to render_ner_analytics_section
content = content.replace(
    "def render_ner_analytics_section(",
    "@st_fragment\ndef render_ner_analytics_section("
)

# In case there are multiple identical replacements, they all get the decorator.
# However, if it was already decorated previously, it would get duplicate decorators.
# So let's clean up any double decorators just in case.
content = content.replace(
    "@st.cache_data(show_spinner=False, max_entries=10)\n@st.cache_data(show_spinner=False, max_entries=10)",
    "@st.cache_data(show_spinner=False, max_entries=10)"
)
content = content.replace(
    "@st_fragment\n@st_fragment",
    "@st_fragment"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully')
