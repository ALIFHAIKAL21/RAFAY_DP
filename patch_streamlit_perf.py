import re

file_path = 'c:\\Ngoding\\Skripsi\\IDP_RAFAY\\Skripsi_rafay_IDP\\stage2_pair_visual_test.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add st_fragment
import_target = '''import pandas as pd
import streamlit as st'''

import_replacement = '''import pandas as pd
import streamlit as st

def get_st_fragment():
    if hasattr(st, "fragment"):
        return st.fragment
    if hasattr(st, "experimental_fragment"):
        return st.experimental_fragment
    return lambda f: f

st_fragment = get_st_fragment()'''

content = content.replace(import_target, import_replacement)

# 2. Wrap matcher UI in st_fragment
ui_target = '''            if reconciliation_rows:
                render_stage2_official_metric_summary(
                    metric_rows,
                    title=reconciliation_title,
                )
                detail_cols = st.columns([1.0, 0.8, 3.0])
                detail_filter = detail_cols[0].selectbox(
                    "Detail pencocokan",
                    [
                        "MATCH benar + Semua Kesalahan",
                        "Semua",
                        "Benar",
                        "Salah",
                        "True Positive (MATCH Benar)",
                        "True Negative (NO_MATCH Benar)",
                        "False Positive (Salah Deteksi)",
                        "False Negative (Gagal Deteksi)",
                    ],
                    index=0,
                    key="stage2_pair_card_filter",
                )
                detail_limit_raw = detail_cols[1].selectbox(
                    "Jumlah card",
                    [5, 10, 20, 50, "Semua"],
                    index=1,
                    key="stage2_pair_card_limit",
                )
                detail_rows = filter_stage2_pair_detail_rows(
                    reconciliation_rows,
                    str(detail_filter),
                )
                detail_limit = len(detail_rows) if detail_limit_raw == "Semua" else int(detail_limit_raw)
                render_stage2_pair_cards(detail_rows, max_cards=detail_limit)
            else:'''

ui_replacement = '''            if reconciliation_rows:
                render_stage2_official_metric_summary(
                    metric_rows,
                    title=reconciliation_title,
                )
                
                @st_fragment
                def render_interactive_pair_cards(metric_rows_data):
                    detail_cols = st.columns([1.0, 0.8, 3.0])
                    detail_filter = detail_cols[0].selectbox(
                        "Detail pencocokan",
                        [
                            "MATCH benar + Semua Kesalahan",
                            "Semua",
                            "Benar",
                            "Salah",
                            "True Positive (MATCH Benar)",
                            "True Negative (NO_MATCH Benar)",
                            "False Positive (Salah Deteksi)",
                            "False Negative (Gagal Deteksi)",
                        ],
                        index=0,
                        key="stage2_pair_card_filter",
                    )
                    detail_limit_raw = detail_cols[1].selectbox(
                        "Jumlah card",
                        [5, 10, 20, 50, "Semua"],
                        index=1,
                        key="stage2_pair_card_limit",
                    )
                    detail_rows = filter_stage2_pair_detail_rows(
                        metric_rows_data,
                        str(detail_filter),
                    )
                    detail_limit = len(detail_rows) if detail_limit_raw == "Semua" else int(detail_limit_raw)
                    render_stage2_pair_cards(detail_rows, max_cards=detail_limit)
                
                render_interactive_pair_cards(reconciliation_rows)
            else:'''

content = content.replace(ui_target, ui_replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
