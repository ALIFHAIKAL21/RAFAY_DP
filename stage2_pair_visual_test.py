from __future__ import annotations

import json
import re
import sys
from html import escape
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd
import streamlit as st
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoTokenizer,
)


ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

DEFAULT_MODEL_PATH = (
    ROOT_DIR / "models" / "indobenchmark" / "indobert-base-p2_15k" / "final_model"
)
DEFAULT_DATASET_PATH = (
    ROOT_DIR / "data" / "chat" / "processed" / "SPC" / "stage2_completion_matcher_dataset.json"
)
DEFAULT_NER_MODEL_PATH = ROOT_DIR / "models" / "indobert_NER" / "final_model"
DEFAULT_NEW_ORDER_SAMPLE_PATH = ROOT_DIR / "test_case" / "pesanan_baru" / "test_case01.txt"

# Temporary switch: keep normalization/standardization code in place, but render and
# analytics should use raw NER extraction output while this is disabled.
OPERATIONAL_NORMALIZATION_ENABLED = False
STAGE2_STRONG_MATCH_THRESHOLD = 0.85
STAGE2_REVIEW_MATCH_THRESHOLD = 0.50
STAGE2_CLEAR_NEW_ORDER_MAX_MATCH = 0.20
STAGE2_AUDIT_SAVE_LIMIT = 5

try:
    from db.persistence import apply_stage2_match_fill as db_apply_stage2_match_fill
    from db.persistence import find_raw_chat_id as db_find_raw_chat_id
    from db.persistence import load_all_order_rows as db_load_all_order_rows
    from db.persistence import load_all_raw_chat_records as db_load_all_raw_chat_records
    from db.persistence import load_all_raw_chat_texts as db_load_all_raw_chat_texts
    from db.persistence import load_latest_raw_chat_text as db_load_latest_raw_chat_text
    from db.persistence import load_stage2_match_audits as db_load_stage2_match_audits
    from db.persistence import prepare_chat_for_parsing as db_prepare_chat_for_parsing
    from db.persistence import replace_parsed_rows as db_replace_parsed_rows
    from db.persistence import reset_all_data as db_reset_all_data
    from db.persistence import save_parsed_rows as db_save_parsed_rows
    from db.persistence import save_stage2_match_audits as db_save_stage2_match_audits
    from db.session import init_db as db_init_db

    DB_PERSISTENCE_ENABLED = True
except Exception:
    db_apply_stage2_match_fill = None
    db_find_raw_chat_id = None
    db_load_all_order_rows = None
    db_load_all_raw_chat_records = None
    db_load_all_raw_chat_texts = None
    db_load_latest_raw_chat_text = None
    db_load_stage2_match_audits = None
    db_prepare_chat_for_parsing = None
    db_replace_parsed_rows = None
    db_reset_all_data = None
    db_save_parsed_rows = None
    db_save_stage2_match_audits = None
    db_init_db = None
    DB_PERSISTENCE_ENABLED = False

LABEL_MATCH = "MATCH"
LABEL_NO_MATCH = "NO_MATCH"
STAGE2_STATUS_CONFLICT = "CONFLICT"
EXCEL_COLUMNS = [
    "No.",
    "Tgl RO",
    "Tgl Muat",
    "Pickup",
    "Tujuan",
    "No. Plat",
    "Type Truck",
    "Driver",
    "Kontak Driver",
]


@dataclass(frozen=True)
class PairCase:
    case_id: str
    group: str
    expected: str
    severity: str
    focus: str
    gate: str
    text_a: str
    text_b: str


@dataclass(frozen=True)
class Stage2OrderCandidate:
    candidate_key: str
    summary: str
    text_a: str
    qty_target: int
    filled: int
    empty: int
    pickup: str
    tujuan: str
    type_truck: str
    tgl_ro: str
    identity_keys: tuple[str, ...]
    source_chat_text: str = ""
    source_chat_rows: tuple[Dict[str, str], ...] = ()
    snapshot_rows: tuple[Dict[str, str], ...] = ()


def clean_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", str(text or "").strip())


def case(
    case_id: str,
    group: str,
    expected: str,
    severity: str,
    focus: str,
    gate: str,
    text_a: str,
    text_b: str,
) -> PairCase:
    return PairCase(
        case_id=case_id,
        group=group,
        expected=expected,
        severity=severity,
        focus=focus,
        gate=gate,
        text_a=clean_text(text_a),
        text_b=clean_text(text_b),
    )


def build_operational_cases() -> List[PairCase]:
    return [
        case(
            "C1-01",
            "Case 1 - progresif 5 unit",
            LABEL_MATCH,
            "HIGH",
            "Awal 1/5, susulan isi 2 slot baru",
            "ALLOW_MERGE",
            """
            [05.31, 7/3/2026] Akbar Rafay: REQUESTT ORDER ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu loading : 02.00 23-03-2026
            Rute/tujuan : CGK - PKU
            DRIVERR  : sutrisno
            Nopol : BM 8496 AU
            No hp : 085364721905
            """,
            """
            [05.31, 7/3/2026] Akbar Rafay: REQUESTT ORDER ULANG DAN TAMBAHAN ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu loading : 03.00
            Rute/tujuan : CGK - PKU
            DRIVERR  : agung
            Nopol : BM 8496 AA
            No hp : 085364721908

            Waktu loading : 04.00
            Rute/tujuan : CGK - PKU
            DRIVERR  : ADRI
            Nopol : BM 8496 ZZ
            No hp : 0853647219918
            """,
        ),
        case(
            "C1-02",
            "Case 1 - progresif 5 unit",
            LABEL_MATCH,
            "HIGH",
            "Susulan ulang berisi duplikat dan slot baru",
            "ALLOW_MERGE_RECHECK_DEDUP",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 3/5 | Sisa slot: 2
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            Unit terdata:
            02.00 23-03-2026 | SUTRISNO | BM 8496 AU | 085364721905
            03.00 | AGUNG | BM 8496 AA | 085364721908
            04.00 | ADRI | BM 8496 ZZ | 0853647219918
            """,
            """
            REQUESTT ORDER ULANG DAN TAMBAHAN ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu loading : 02.00 23-03-2026
            Rute/tujuan : CGK - PKU
            DRIVERR  : DANDI
            Nopol : BM 8496 ZX
            No hp : 085364721993

            Waktu loading : 03.00
            Rute/tujuan : CGK - PKU
            DRIVERR  : agung
            Nopol : BM 8496 AA
            No hp : 085364721908

            Waktu loading : 03.00
            Rute/tujuan : CGK - PKU
            DRIVERR  : AJENG
            Nopol : BM 8496 AR
            No hp : 0853647229304
            """,
        ),
        case(
            "C1-03",
            "Case 1 - progresif 5 unit",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Tanggal request beda, field lain sama",
            "BLOCK_DATE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 3/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQUEST ORDER ULANG ONCALL 23 MARET 2026
            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu loading : 03.00
            Rute/tujuan : CGK - PKU
            driver : AGUNG
            Nopol : BM 8496 AA
            No hp : 085364721908
            """,
        ),
        case(
            "C1-04",
            "Case 1 - progresif 5 unit",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Rute beda dengan lokasi, tanggal, tipe sama",
            "BLOCK_ROUTE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 1/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQUEST ORDER ULANG DAN TAMBAHAN ONCALL 22 MARET 2026
            5 UNIT TWB 50 CBM
            Lokasi : ARGOPANTES
            Waktu lodng : 04.00
            Rute/tujuan : CGK - PDG
            DRVER : JUNA
            Nopol : BM 9012 TX
            No hp : 081382430111
            """,
        ),
        case(
            "C1-05",
            "Case 1 - progresif 5 unit",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Lokasi beda dengan tanggal, rute, tipe sama",
            "BLOCK_LOCATION_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 1/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQUEST ORDER ULANG ONCALL 22 MARET 2026
            5 UNIT TWB 50 CBM
            Loksi : MEGAHUB
            Waktu loading : 04.00
            Rute/tujuan : CGK - PKU
            driver : JUNA
            Nopol : BM 9012 TX
            No hp : 081382430111
            """,
        ),
        case(
            "C1-06",
            "Case 1 - progresif 5 unit",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Order sudah 5/5 lalu ada unit ke-6",
            "BLOCK_OVER_TARGET",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 5/5 | Sisa slot: 0
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            Unit terdata:
            SUTRISNO BM 8496 AU; AGUNG BM 8496 AA; ADRI BM 8496 ZZ; DANDI BM 8496 ZX; AJENG BM 8496 AR
            """,
            """
            REQUEST ORDER ULANG DAN TAMBAHAN ONCALL 22 MARET 2026
            5 UNIT TWB 50 CBM
            Lokasi : ARGOPANTES
            Waktu loading : 05:00
            Rute/tujuan : CGK - PKU
            driver : BIMA
            Nopol : BM 8496 QR
            No hp : 085364729999
            """,
        ),
        case(
            "C2-01",
            "Case 2 - awal 2 susulan 3",
            LABEL_MATCH,
            "HIGH",
            "Awal 2/5, susulan 3 driver lengkap",
            "ALLOW_MERGE",
            """
            [05.31, 7/3/2026] Akbar Rafay: REQEST ORDER ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu lodng : 15:00
            Rute/tujuan : CGK - PKU
            DRIVERR  : IWAN
            Nopol  : B 9702 TX
            No hp  :087844620137

            Waktu loading : 18:00
            Rute/tujuan : CGK - PKU
            DRVER  : MARTIN
            Nopol  : B 9357 FXR
            No hp  :81382430619
            """,
            """
            [05.31, 7/3/2026] Akbar Rafay: REQEST ORDER ULANG DAN TAMBAHAN ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu lodng : 15:00
            Rute/tujuan : CGK - PKU
            DRIVERR  : RANDI
            Nopol  : B 9702 XX
            No hp  :0878446223834

            Waktu loading : 14:00
            Rute/tujuan : CGK - PKU
            DRVER  : AHMAD
            Nopol  : B 9357 TT
            No hp  :81382428374

            Waktu loading : 14:00
            Rute/tujuan : CGK - PKU
            DRVER  : JUNAM
            Nopol  : B 9357 ARG
            No hp  :81382422849
            """,
        ),
        case(
            "C2-02",
            "Case 2 - awal 2 susulan 3",
            LABEL_MATCH,
            "MEDIUM",
            "Header hanya REQUEST ORDER ULANG ONCALL",
            "ALLOW_MERGE",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 2/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQEST ORDER ULANG ONCALL 22 MARET 2026
            5 UNIT TWB 50 CBM
            Lokasi : ARGOPANTES
            Waktu loading : 13:30
            Rute/tujuan : CGK - PKU
            driver : YUSUF
            Nopol : B 9001 FX
            No hp : 081112223333
            """,
        ),
        case(
            "C2-03",
            "Case 2 - awal 2 susulan 3",
            LABEL_MATCH,
            "MEDIUM",
            "Susulan tanpa header baku dengan noise chat",
            "ALLOW_MERGE_REVIEW_NO_HEADER",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 2/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            bang ini tambahan buat argopantes pku ya, sisanya nyusul:
            5 unit twb 50 cbm
            lokasi argopantes
            wktu loding 16.30
            tujuan CGK - PKU
            sopir : HAFIZ
            plat : BM 8891 KX
            kontak : 081255667700
            """,
        ),
        case(
            "C2-04",
            "Case 2 - awal 2 susulan 3",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Tipe unit beda",
            "BLOCK_UNIT_TYPE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 2/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQUEST ORDER ULANG ONCALL 22 MARET 2026
            5 UNIT CDD 24 CBM
            Lokasi : ARGOPANTES
            Waktu loading : 16:30
            Rute/tujuan : CGK - PKU
            driver : HAFIZ
            Nopol : BM 8891 KX
            No hp : 081255667700
            """,
        ),
        case(
            "C3-01",
            "Case 3 - slot kosong eksplisit",
            LABEL_MATCH,
            "HIGH",
            "Awal 1 lengkap, 4 slot kosong, susulan isi 2",
            "ALLOW_MERGE",
            """
            [05.31, 7/3/2026] Akbar Rafay: REQEST ORDER ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu lodng : 15:00
            Rute/tujuan : CGK - PKU
            DRIVERR  : IWAN
            Nopol  : B 9702 TX
            No hp  :087844620137

            Waktu loading : 18:00
            Rute/tujuan : CGK - PKU
            DRVER  :
            Nopol  :
            No hp  :

            Waktu loading : 17:00
            Rute/tujuan : CGK - PKU
            DRVER  :
            Nopol  :
            No hp  :
            """,
            """
            REQEST ORDER ULANG DAN TAMABAHAN ONCALL 22 MARET 2026:

            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu lodng : 15:00
            Rute/tujuan : CGK - PKU
            DRIVERR  : IWAN
            Nopol  : B 9702 TX
            No hp  :087844620137

            Waktu loading : 18:00
            Rute/tujuan : CGK - PKU
            DRVER  : ANDI
            Nopol  : I 888 AX
            No hp  : 0293848471882

            Waktu loading : 17:00
            Rute/tujuan : CGK - PKU
            DRVER  : RANDO
            Nopol  : A 1234 AX
            No hp  : 029383112
            """,
        ),
        case(
            "C3-02",
            "Case 3 - slot kosong eksplisit",
            LABEL_MATCH,
            "MEDIUM",
            "Full resend berisi slot kosong sisa",
            "ALLOW_MERGE_SKIP_EMPTY_SLOT",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 1/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQEST ORDER ULANG DAN TAMABAHAN ONCALL 22 MARET 2026:
            5 UNIT TWB 50 Cbm
            Lokasi : ARGOPANTES
            Waktu loading : 18:00
            Rute/tujuan : CGK - PKU
            DRVER  : ANDI
            Nopol  : I 888 AX
            No hp  : 0293848471882

            Waktu loading : 19:00
            Rute/tujuan : CGK - PKU
            DRVER  :
            Nopol  :
            No hp  :
            """,
        ),
        case(
            "C3-03",
            "Case 3 - slot kosong eksplisit",
            LABEL_NO_MATCH,
            "MEDIUM",
            "Hanya slot kosong tanpa data baru",
            "BLOCK_NO_NEW_DRIVER_DATA",
            """
            ORDER_STATE | Tanggal request: 22 MARET 2026 | Qty target: 5 | Terisi: 1/5
            Unit: TWB 50 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - PKU
            """,
            """
            REQUEST ORDER ULANG ONCALL 22 MARET 2026
            5 UNIT TWB 50 CBM
            Lokasi : ARGOPANTES
            Waktu loading : 18:00
            Rute/tujuan : CGK - PKU
            driver :
            Nopol :
            No hp :
            """,
        ),
        case(
            "M1-01",
            "Multi order line - Jateng Jatim",
            LABEL_MATCH,
            "HIGH",
            "Satu pesan berisi dua rute terpisah, susulan isi keduanya",
            "ALLOW_MERGE_SPLIT_BY_ROUTE",
            """
            REQUEST ORDER ONCALL 02 JUNI 2026:

            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATENG
            driver  :
            Nopol  :
            No HP :

            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATIM
            driver  :
            Nopol  :
            No HP :
            """,
            """
            REQUEST ORDER ONCALL 02 JUNI 2026:

            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATENG
            driver : Agus / dian
            Nopol : AD 8857 DV
            No HP :+62 815-5952-1259

            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATIM
            driver : AGUNG
            Nopol : B 555 AX
            No HP : 081574673448
            """,
        ),
        case(
            "M1-02",
            "Multi order line - Jateng Jatim",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Candidate JATENG dibanding susulan JATIM",
            "BLOCK_ROUTE_MISMATCH",
            """
            ORDER_LINE | Tanggal request: 02 JUNI 2026 | Qty target: 1 | Terisi: 0/1
            Unit: CDDL 24 CBM | Lokasi: MEGAHUB | Rute/tujuan: CGK - JATENG | Waktu loading: 23:00
            """,
            """
            REQUEST ORDER ONCALL 02 JUNI 2026
            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATIM
            driver : AGUNG
            Nopol : B 555 AX
            No HP : 081574673448
            """,
        ),
        case(
            "M1-03",
            "Multi order line - Jateng Jatim",
            LABEL_MATCH,
            "HIGH",
            "Candidate JATIM cocok dengan susulan JATIM",
            "ALLOW_MERGE",
            """
            ORDER_LINE | Tanggal request: 02 JUNI 2026 | Qty target: 1 | Terisi: 0/1
            Unit: CDDL 24 CBM | Lokasi: MEGAHUB | Rute/tujuan: CGK - JATIM | Waktu loading: 23:00
            """,
            """
            REQUEST ORDER ONCALL 02 JUNI 2026
            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATIM
            driver : AGUNG
            Nopol : B 555 AX
            No HP : 081574673448
            """,
        ),
        case(
            "M1-04",
            "Multi order line - Jateng Jatim",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Tanggal beda pada order line yang field lain sama",
            "BLOCK_DATE_MISMATCH",
            """
            ORDER_LINE | Tanggal request: 02 JUNI 2026 | Qty target: 1 | Terisi: 0/1
            Unit: CDDL 24 CBM | Lokasi: MEGAHUB | Rute/tujuan: CGK - JATIM | Waktu loading: 23:00
            """,
            """
            REQUEST ORDER ONCALL 03 JUNI 2026
            1 unit Cddl 24 Cbm
            Lokasi : Megahub
            Waktu loading : 23:00
            Rute/tujuan : CGK - JATIM
            driver : AGUNG
            Nopol : B 555 AX
            No HP : 081574673448
            """,
        ),
        case(
            "Q1-01",
            "Quantity 1-20",
            LABEL_MATCH,
            "MEDIUM",
            "Single unit empty menjadi lengkap",
            "ALLOW_MERGE",
            """
            REQUEST ORDER ONCALL 06 FEB 2026
            1 UNIT CDD 24 CBM
            Lokasi : CIKARANG
            Waktu loading : SEGERA
            Rute/tujuan : CGK - SUB
            driver :
            Nopol :
            No hp :
            """,
            """
            Request ulang oncall 06 feb 2026
            1 unit cdd 24 cbm
            lokasi cikarang
            waktu loading segera
            rute/tujuan CGK - SUB
            driver : HENDRA S.P
            nopol : D 9044 AG
            no hp : +62 877-8667-6177
            """,
        ),
        case(
            "Q1-02",
            "Quantity 1-20",
            LABEL_MATCH,
            "MEDIUM",
            "Target 12 unit, susulan 5 unit",
            "ALLOW_MERGE",
            """
            ORDER_STATE | Tanggal request: 09 APRIL 2026 | Qty target: 12 | Terisi: 7/12 | Sisa slot: 5
            Unit: CDD LONG 32 CBM | Lokasi: KIIC | Rute/tujuan: CGK - SBY
            """,
            """
            info tambahan oncall 09 april 2026
            12 unit cdd long 32 cbm
            lokasi : KIIC
            waktu loading : 21:00
            rute/tujuan : CGK - SBY
            driver : TEGUH
            nopol : B 7012 UX
            no hp : 081900112211

            waktu loading : 22:00
            rute/tujuan : CGK - SBY
            driver : DARMA
            nopol : L 7721 ZQ
            no hp : 081900113322
            """,
        ),
        case(
            "Q1-03",
            "Quantity 1-20",
            LABEL_MATCH,
            "MEDIUM",
            "Target 20 unit, susulan noise tanpa header",
            "ALLOW_MERGE_REVIEW_NO_HEADER",
            """
            ORDER_STATE | Tanggal request: 18 MEI 2026 | Qty target: 20 | Terisi: 14/20
            Unit: FUSO 55 CBM | Lokasi: SUNTER | Rute/tujuan: CGK - MDN
            """,
            """
            pak yg sunter medan 18 mei lanjut 3 armada dulu
            20 unit fuso 55 cbm
            lks : sunter
            jam muat : 01:00
            tujuan : CGK - MDN
            nama : YOGA
            nopol : BK 8812 AA
            no wa : 081277771111
            """,
        ),
        case(
            "Q1-04",
            "Quantity 1-20",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Qty target berbeda dan order state sudah penuh",
            "BLOCK_OVER_TARGET_OR_NEW_ORDER",
            """
            ORDER_STATE | Tanggal request: 18 MEI 2026 | Qty target: 20 | Terisi: 20/20 | Sisa slot: 0
            Unit: FUSO 55 CBM | Lokasi: SUNTER | Rute/tujuan: CGK - MDN
            """,
            """
            request order oncall 18 mei 2026
            8 unit fuso 55 cbm
            lokasi : sunter
            waktu loading : 01:00
            rute/tujuan : CGK - MDN
            driver : YOGA
            nopol : BK 8812 AA
            no hp : 081277771111
            """,
        ),
        case(
            "N1-01",
            "Typo dan noise lapangan",
            LABEL_MATCH,
            "MEDIUM",
            "Typo header dan label field",
            "ALLOW_MERGE",
            """
            ORDER_STATE | Tanggal request: 06 FEBRUARI 2026 | Qty target: 5 | Terisi: 3/5
            Unit: CDDL 24 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - JATIM TENTATIF
            """,
            """
            REQUER ORDER ULANG DAN TAMBAHAN ON CALL 06 FEBUARI 2026
            5 UNIT CDDL/24 CBM
            Loksi : ARGOPANTES
            Waktu lodng : SEGERA
            Rute tujan : CGK - JATIM TENTATIF
            DRVER : LATIF
            Nopel : L 6754 ZZ
            No tlp : +62 852-8278-1670
            """,
        ),
        case(
            "N1-02",
            "Typo dan noise lapangan",
            LABEL_MATCH,
            "MEDIUM",
            "Chat timestamp beda, tanggal request sama",
            "ALLOW_MERGE",
            """
            [21.18, 1/6/2026] Admin: REQUEST ORDER ONCALL 06 FEB 2026
            5 UNIT CDDL/24 CBM
            Lokasi : ARGOPANTES
            Rute/tujuan : CGK - JATIM TENTATIF
            driver : Adip
            Nopol : B 3309 AU
            No hp : +62 852-4568-1444
            """,
            """
            [09.12, 2/6/2026] Operasional: tambahan yg argopantes jatim tentatif
            REQ ORDER ULANG ONCALL 06 FEB 2026
            5 UNIT CDDL 24 CBM
            lokasi : ARGOPANTES
            rute tujuan : CGK - JATIM TENTATIF
            driver : HANIF
            nopol : L 7823 ZZ
            no hp : +62 852-8278-910
            """,
        ),
        case(
            "N1-03",
            "Typo dan noise lapangan",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Typo berat tapi tanggal beda",
            "BLOCK_DATE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 06 FEBRUARI 2026 | Qty target: 5 | Terisi: 3/5
            Unit: CDDL 24 CBM | Lokasi: ARGOPANTES | Rute/tujuan: CGK - JATIM TENTATIF
            """,
            """
            REQUER ORDER ULANG ON CALL 07 FEBUARI 2026
            5 UNIT CDDL/24 CBM
            Loksi : ARGOPANTES
            Waktu lodng : SEGERA
            Rute tujan : CGK - JATIM TENTATIF
            DRVER : LATIF
            Nopel : L 6754 ZZ
            No tlp : +62 852-8278-1670
            """,
        ),
        case(
            "N1-04",
            "Typo dan noise lapangan",
            LABEL_NO_MATCH,
            "HIGH",
            "Non atribut mirip tapi rute beda tipis",
            "BLOCK_ROUTE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 11 JULI 2026 | Qty target: 4 | Terisi: 2/4
            Unit: CDE 20 CBM | Lokasi: DAAN MOGOT | Rute/tujuan: CGK - BDG
            """,
            """
            ini yg daan mogot ya min, tambahan sore
            request ulang oncal 11 juli 2026
            4 unit cde 20 cbm
            lokasi : daan mogot
            waktu loading : 17:00
            rute/tujuan : CGK - BGR
            driver : ARDI
            nopol : B 7099 JP
            no hp : 081288882222
            """,
        ),
        case(
            "D1-01",
            "Duplikat dan resend",
            LABEL_MATCH,
            "MEDIUM",
            "Resend data yang sama pada order yang sama",
            "ALLOW_MATCH_SKIP_DUPLICATE",
            """
            ORDER_STATE | Tanggal request: 12 AGUSTUS 2026 | Qty target: 3 | Terisi: 1/3
            Unit: WINGBOX 60 CBM | Lokasi: CIBITUNG | Rute/tujuan: CGK - SLO
            Unit terdata: 20:00 | RIZKY | B 7788 KX | 081212121212
            """,
            """
            REQUEST ORDER ULANG ONCALL 12 AGUSTUS 2026
            3 UNIT WINGBOX 60 CBM
            Lokasi : CIBITUNG
            Waktu loading : 20:00
            Rute/tujuan : CGK - SLO
            driver : RIZKY
            Nopol : B 7788 KX
            No hp : 081212121212
            """,
        ),
        case(
            "D1-02",
            "Duplikat dan resend",
            LABEL_NO_MATCH,
            "CRITICAL",
            "Nopol sama tetapi order route berbeda",
            "BLOCK_ROUTE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 12 AGUSTUS 2026 | Qty target: 3 | Terisi: 1/3
            Unit: WINGBOX 60 CBM | Lokasi: CIBITUNG | Rute/tujuan: CGK - SLO
            """,
            """
            REQUEST ORDER ULANG ONCALL 12 AGUSTUS 2026
            3 UNIT WINGBOX 60 CBM
            Lokasi : CIBITUNG
            Waktu loading : 20:00
            Rute/tujuan : CGK - SMG
            driver : RIZKY
            Nopol : B 7788 KX
            No hp : 081212121212
            """,
        ),
        case(
            "T1-01",
            "Waktu loading variatif",
            LABEL_MATCH,
            "MEDIUM",
            "Waktu loading beda tetapi order sama",
            "ALLOW_MERGE",
            """
            ORDER_STATE | Tanggal request: 15 SEPTEMBER 2026 | Qty target: 6 | Terisi: 3/6
            Unit: TRONTON 45 CBM | Lokasi: KARAWANG | Rute/tujuan: CGK - MLG
            Waktu loading awal: SEGERA, 21:00, 00:00
            """,
            """
            REQUEST ORDER ULANG DAN TAMBAHAN ONCALL 15 SEPT 2026
            6 UNIT TRONTON 45 CBM
            Lokasi : KARAWANG
            Waktu loading : 03:00 16/09/2026
            Rute/tujuan : CGK - MLG
            driver : BUDI
            Nopol : N 4321 EF
            No Hp : 08987654321
            """,
        ),
        case(
            "T1-02",
            "Waktu loading variatif",
            LABEL_NO_MATCH,
            "HIGH",
            "Waktu mirip, tanggal request beda",
            "BLOCK_DATE_MISMATCH",
            """
            ORDER_STATE | Tanggal request: 15 SEPTEMBER 2026 | Qty target: 6 | Terisi: 3/6
            Unit: TRONTON 45 CBM | Lokasi: KARAWANG | Rute/tujuan: CGK - MLG
            """,
            """
            REQUEST ORDER ULANG DAN TAMBAHAN ONCALL 16 SEPT 2026
            6 UNIT TRONTON 45 CBM
            Lokasi : KARAWANG
            Waktu loading : 03:00
            Rute/tujuan : CGK - MLG
            driver : BUDI
            Nopol : N 4321 EF
            No Hp : 08987654321
            """,
        ),
    ]


MONTHS = {
    "JAN": 1,
    "JANUARI": 1,
    "JANUARY": 1,
    "FEB": 2,
    "FEBUARI": 2,
    "FEBRUARI": 2,
    "FEBUARY": 2,
    "FEBRUARY": 2,
    "MAR": 3,
    "MARET": 3,
    "MARCH": 3,
    "APR": 4,
    "APRIL": 4,
    "MEI": 5,
    "MAY": 5,
    "JUN": 6,
    "JUNI": 6,
    "JUNE": 6,
    "JUL": 7,
    "JULI": 7,
    "JULY": 7,
    "AGU": 8,
    "AGS": 8,
    "AGUSTUS": 8,
    "AUG": 8,
    "AUGUST": 8,
    "SEP": 9,
    "SEPT": 9,
    "SEPTEMBER": 9,
    "OKT": 10,
    "OKTOBER": 10,
    "OCT": 10,
    "NOV": 11,
    "NOVEMBER": 11,
    "DES": 12,
    "DESEMBER": 12,
    "DEC": 12,
    "DECEMBER": 12,
}

MONTH_FULL_NAMES = {
    1: "JANUARI",
    2: "FEBRUARI",
    3: "MARET",
    4: "APRIL",
    5: "MEI",
    6: "JUNI",
    7: "JULI",
    8: "AGUSTUS",
    9: "SEPTEMBER",
    10: "OKTOBER",
    11: "NOVEMBER",
    12: "DESEMBER",
}


def canonical_month_token(token: str) -> str:
    text = re.sub(r"[^A-Z]", "", str(token or "").upper())
    text = re.sub(r"([A-Z])\1+", r"\1", text)
    return text.replace("FEBUARY", "FEBRUARI").replace("FEBUARI", "FEBRUARI")


def month_id_from_token(token: str) -> int | None:
    normalized = canonical_month_token(token)
    return MONTHS.get(normalized)


def stage2_normalize_dates_for_model(text: str) -> str:
    source = str(text or "")

    def word_repl(match: re.Match) -> str:
        day = int(match.group(1))
        month_id = month_id_from_token(match.group(2))
        if not month_id:
            return match.group(0)
        year = int(match.group(3))
        if year < 100:
            year += 2000
        return f"{day:02d} {MONTH_FULL_NAMES[month_id]} {year:04d}"

    def numeric_repl(match: re.Match) -> str:
        day = int(match.group(1))
        month_id = int(match.group(2))
        year = int(match.group(3))
        if not (1 <= day <= 31 and 1 <= month_id <= 12):
            return match.group(0)
        if year < 100:
            year += 2000
        return f"{day:02d} {MONTH_FULL_NAMES[month_id]} {year:04d}"

    normalized = re.sub(
        r"\b(\d{1,2})[\s./-]+([A-Za-z]{3,15})[\s./-]+(\d{2,4})\b",
        word_repl,
        source,
    )
    normalized = re.sub(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        numeric_repl,
        normalized,
    )
    return normalized


def normalize_value(value: str) -> str:
    value = str(value or "").upper()
    value = stage2_normalize_dates_for_model(value).upper()
    value = re.sub(r"\bON\s+CALL\b", "ONCALL", value)
    value = re.sub(r"[^A-Z0-9]+", "", value)
    return value


def normalize_route(value: str) -> str:
    value = str(value or "").upper()
    value = value.replace("TENTATIVE", "TENTATIF")
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" - ", "-").replace(" -", "-").replace("- ", "-")
    return normalize_value(value)


def find_date_tokens(text: str) -> List[str]:
    s = str(text or "").upper()
    found: List[str] = []

    word_pattern = r"\b(\d{1,2})[\s./-]+([A-Z]{3,15})[\s./-]+(\d{2,4})\b"
    for day, month, year in re.findall(word_pattern, s):
        month_id = month_id_from_token(month)
        if month_id:
            year_int = int(year)
            if year_int < 100:
                year_int += 2000
            found.append(f"{year_int:04d}-{month_id:02d}-{int(day):02d}")

    for day, month, year in re.findall(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", s):
        day_int = int(day)
        month_int = int(month)
        year_int = int(year)
        if year_int < 100:
            year_int += 2000
        if 1 <= day_int <= 31 and 1 <= month_int <= 12:
            found.append(f"{year_int:04d}-{month_int:02d}-{day_int:02d}")

    return list(dict.fromkeys(found))


def extract_request_date(text: str) -> str:
    s = str(text or "")
    explicit = re.search(
        r"(?is)\btanggal\s*request\s*[:=]\s*([^\n|]+)",
        s,
    )
    if explicit:
        dates = find_date_tokens(explicit.group(1))
        if dates:
            return dates[0]

    header = re.search(r"(?is)\bon\s*call\b(.{0,90})", s)
    if header:
        dates = find_date_tokens(header.group(1))
        if dates:
            return dates[0]

    dates = find_date_tokens(s)
    return dates[0] if dates else ""


def ro_date_has_month_year_without_day(value: str) -> bool:
    text = stage2_normalize_dates_for_model(str(value or "")).upper()
    if not text.strip():
        return False
    month_pattern = "|".join(sorted((re.escape(key) for key in MONTHS), key=len, reverse=True))
    has_full_date = bool(
        re.search(rf"\b\d{{1,2}}\s+(?:{month_pattern})\s+\d{{2,4}}\b", text)
        or re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    )
    if has_full_date:
        return False
    return bool(re.search(rf"\b(?:{month_pattern})\s+\d{{2,4}}\b", text))


def month_year_key_from_text(value: str) -> tuple[int | None, int | None]:
    text = stage2_normalize_dates_for_model(str(value or "")).upper()
    month_pattern = "|".join(sorted((re.escape(key) for key in MONTHS), key=len, reverse=True))
    match = re.search(rf"\b(?:\d{{1,2}}\s+)?({month_pattern})\s+(\d{{2,4}})\b", text)
    if not match:
        return None, None
    month_id = month_id_from_token(match.group(1))
    year = int(match.group(2))
    if year < 100:
        year += 2000
    return month_id, year


def display_request_date_from_iso(iso_date: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(iso_date or "").strip())
    if not match:
        return ""
    year = int(match.group(1))
    month_id = int(match.group(2))
    day = int(match.group(3))
    month_name = MONTH_FULL_NAMES.get(month_id)
    if not month_name:
        return ""
    return f"{day:02d} {month_name.lower()} {year:04d}"


def repair_ro_date_from_header(ro_date: str, chunk_text: str) -> str:
    ro_date = str(ro_date or "").strip()
    if not ro_date_has_month_year_without_day(ro_date):
        return ro_date

    request_date = extract_request_date(chunk_text)
    if not request_date:
        return ro_date

    ro_month, ro_year = month_year_key_from_text(ro_date)
    req_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", request_date)
    if not req_match:
        return ro_date
    req_year = int(req_match.group(1))
    req_month = int(req_match.group(2))
    if ro_month and ro_year and (ro_month != req_month or ro_year != req_year):
        return ro_date

    return display_request_date_from_iso(request_date) or ro_date


def field_values(text: str, labels: Sequence[str]) -> List[str]:
    joined = "|".join(labels)
    pattern = rf"(?im)^\s*(?:{joined})\s*[:=]?\s*(.+?)\s*$"
    values = []
    for value in re.findall(pattern, str(text or "")):
        value = value.strip(" |")
        if value and value not in {"-", "_"}:
            values.append(value)
    return list(dict.fromkeys(values))


def first_unit_type(text: str) -> str:
    s = str(text or "")
    m = re.search(
        r"(?is)\b\d{1,2}\s*unit\s+([a-z0-9/ ._-]{2,40}?)(?=\s*(?:lokasi|loksi|loaksi|waktu|rute|route|driver|drver|nopol|\n|$))",
        s,
    )
    if m:
        value = m.group(1)
    else:
        m = re.search(r"(?is)\bunit\s*[:=]\s*([a-z0-9/ ._-]{2,40})", s)
        value = m.group(1) if m else ""
    value = value.replace("/", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return normalize_value(value)


def extract_qty(text: str) -> int | None:
    m = re.search(r"(?is)\bqty\s*target\s*[:=]\s*(\d{1,2})\b", str(text or ""))
    if not m:
        m = re.search(r"(?is)\b(\d{1,2})\s*unit\b", str(text or ""))
    return int(m.group(1)) if m else None


def extract_filled_state(text: str) -> tuple[int | None, int | None]:
    m = re.search(r"(?is)\bterisi\s*[:=]\s*(\d{1,2})\s*/\s*(\d{1,2})\b", str(text or ""))
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def count_filled_driver_records(text: str) -> int:
    labels = [
        "driver",
        "driverr",
        "drver",
        "drivr",
        "nama",
        "sopir",
        "pengemudi",
    ]
    values = field_values(text, labels)
    blacklist = {"", "-", "KOSONG", "NULL", "NONE", "BELUM ADA"}
    return sum(1 for value in values if normalize_value(value) not in blacklist)


def operational_checks(text_a: str, text_b: str) -> Dict[str, str]:
    date_a = extract_request_date(text_a)
    date_b = extract_request_date(text_b)

    loc_a = field_values(text_a, ["lokasi", "loksi", "loaksi", "lks"])
    loc_b = field_values(text_b, ["lokasi", "loksi", "loaksi", "lks"])
    route_a = field_values(
        text_a,
        [
            "rute/tujuan",
            "rute tujuan",
            "rute",
            "route",
            "route/tujuan",
            "tujuan",
        ],
    )
    route_b = field_values(
        text_b,
        [
            "rute/tujuan",
            "rute tujuan",
            "rute",
            "route",
            "route/tujuan",
            "tujuan",
        ],
    )

    type_a = first_unit_type(text_a)
    type_b = first_unit_type(text_b)
    filled_a, target_a = extract_filled_state(text_a)
    qty_a = target_a or extract_qty(text_a)
    qty_b = extract_qty(text_b)
    incoming_records = count_filled_driver_records(text_b)

    advisories = []
    if date_a and date_b and date_a != date_b:
        advisories.append("BLOCK: tanggal request beda")

    loc_set_a = {normalize_value(v) for v in loc_a if normalize_value(v)}
    loc_set_b = {normalize_value(v) for v in loc_b if normalize_value(v)}
    if loc_set_a and loc_set_b and loc_set_a.isdisjoint(loc_set_b):
        advisories.append("BLOCK: lokasi beda")

    route_set_a = {normalize_route(v) for v in route_a if normalize_route(v)}
    route_set_b = {normalize_route(v) for v in route_b if normalize_route(v)}
    if route_set_a and route_set_b and route_set_a.isdisjoint(route_set_b):
        advisories.append("BLOCK: rute/tujuan beda")

    if type_a and type_b and type_a != type_b:
        advisories.append("BLOCK: tipe unit beda")

    if filled_a is not None and qty_a is not None and filled_a >= qty_a and incoming_records:
        advisories.append("BLOCK: target unit sudah penuh")

    if incoming_records == 0:
        advisories.append("REVIEW: pesan susulan tidak punya driver terisi")

    if qty_a and qty_b and qty_a != qty_b:
        advisories.append("REVIEW: angka qty beda")

    return {
        "request_date_a": date_a or "-",
        "request_date_b": date_b or "-",
        "location_a": ", ".join(loc_a[:2]) or "-",
        "location_b": ", ".join(loc_b[:2]) or "-",
        "route_a": ", ".join(route_a[:3]) or "-",
        "route_b": ", ".join(route_b[:3]) or "-",
        "unit_type_a": type_a or "-",
        "unit_type_b": type_b or "-",
        "qty_a": str(qty_a) if qty_a else "-",
        "qty_b": str(qty_b) if qty_b else "-",
        "incoming_driver_records": str(incoming_records),
        "rule_advisory": "; ".join(advisories) if advisories else "OK",
    }


def expected_from_operational_checks(checks: Dict[str, str]) -> str:
    advisory = str(checks.get("rule_advisory", ""))
    if "BLOCK:" in advisory:
        return LABEL_NO_MATCH
    if "tidak punya driver terisi" in advisory:
        return LABEL_NO_MATCH
    return LABEL_MATCH


def result_status(expected: str, predicted: str) -> tuple[str, str, str]:
    if predicted == expected:
        return "PASS", "-", "Prediksi sesuai expected."
    if expected == LABEL_NO_MATCH and predicted == LABEL_MATCH:
        return (
            "FAIL",
            "FALSE_MATCH",
            "Risiko tinggi: model membuka peluang merge ke order yang salah.",
        )
    return (
        "FAIL",
        "FALSE_NO_MATCH",
        "Risiko operasional: pelengkapan benar bisa tertahan sebagai tidak cocok.",
    )


def discover_model_dirs() -> List[str]:
    root = ROOT_DIR / "models"
    if not root.exists():
        return [str(DEFAULT_MODEL_PATH)]

    candidates = []
    for config_path in root.rglob("config.json"):
        parent = config_path.parent
        has_weights = (parent / "model.safetensors").exists() or (
            parent / "pytorch_model.bin"
        ).exists()
        has_tokenizer = (parent / "tokenizer.json").exists() or (
            parent / "vocab.txt"
        ).exists()
        if has_weights and has_tokenizer:
            candidates.append(str(parent))

    candidates = sorted(set(candidates))
    default = str(DEFAULT_MODEL_PATH)
    if default in candidates:
        candidates.remove(default)
        candidates.insert(0, default)
    elif DEFAULT_MODEL_PATH.exists():
        candidates.insert(0, default)
    return candidates or [default]


@st.cache_resource(show_spinner="Loading IndoBERT sequence-pair model...")
def load_model(model_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()
    return tokenizer, model, device


def label_for_id(model, idx: int) -> str:
    id2label = getattr(model.config, "id2label", {}) or {}
    return id2label.get(idx) or id2label.get(str(idx)) or str(idx)


def match_label_id(model) -> int:
    label2id = getattr(model.config, "label2id", {}) or {}
    if LABEL_MATCH in label2id:
        return int(label2id[LABEL_MATCH])
    for idx in range(getattr(model.config, "num_labels", 2)):
        if label_for_id(model, idx).upper() == LABEL_MATCH:
            return idx
    return 1


def predict_pairs(
    tokenizer,
    model,
    device,
    pairs: Sequence[tuple[str, str]],
    max_seq_len: int,
    threshold: float,
    batch_size: int = 8,
) -> List[Dict[str, float | str]]:
    results: List[Dict[str, float | str]] = []
    match_id = match_label_id(model)
    no_match_id = 0 if match_id != 0 else 1

    for start in range(0, len(pairs), batch_size):
        batch = pairs[start : start + batch_size]
        left = [stage2_normalize_dates_for_model(p[0]) for p in batch]
        right = [stage2_normalize_dates_for_model(p[1]) for p in batch]
        inputs = tokenizer(
            left,
            right,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_seq_len,
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).detach().cpu()

        for row in probs:
            p_match = float(row[match_id].item())
            p_no_match = float(row[no_match_id].item()) if no_match_id < len(row) else 1.0 - p_match
            pred = LABEL_MATCH if p_match >= threshold else LABEL_NO_MATCH
            confidence = p_match if pred == LABEL_MATCH else p_no_match
            argmax_id = int(torch.argmax(row).item())
            results.append(
                {
                    "predicted": pred,
                    "argmax_label": label_for_id(model, argmax_id),
                    "p_match": p_match,
                    "p_no_match": p_no_match,
                    "confidence": float(confidence),
                }
            )
    return results


def cases_to_dataframe(
    cases: Sequence[PairCase],
    predictions: Sequence[Dict[str, float | str]],
) -> pd.DataFrame:
    rows = []
    for item, pred in zip(cases, predictions):
        checks = operational_checks(item.text_a, item.text_b)
        expected = item.expected
        predicted = str(pred["predicted"])
        status = "PASS" if predicted == expected else "FAIL"
        error_type = "-"
        if expected == LABEL_NO_MATCH and predicted == LABEL_MATCH:
            error_type = "FALSE_MATCH"
        elif expected == LABEL_MATCH and predicted == LABEL_NO_MATCH:
            error_type = "FALSE_NO_MATCH"

        rows.append(
            {
                "case_id": item.case_id,
                "group": item.group,
                "expected": expected,
                "predicted": predicted,
                "status": status,
                "error_type": error_type,
                "severity": item.severity,
                "p_match": float(pred["p_match"]),
                "p_no_match": float(pred["p_no_match"]),
                "confidence": float(pred["confidence"]),
                "gate": item.gate,
                "focus": item.focus,
                **checks,
                "text_a": item.text_a,
                "text_b": item.text_b,
            }
        )
    return pd.DataFrame(rows)


def metric_bundle(df: pd.DataFrame) -> Dict[str, float | int]:
    if df.empty:
        return {
            "total": 0,
            "pass_rate": 0.0,
            "precision_match": 0.0,
            "recall_match": 0.0,
            "f1_match": 0.0,
            "false_match": 0,
            "false_no_match": 0,
        }

    tp = int(((df["expected"] == LABEL_MATCH) & (df["predicted"] == LABEL_MATCH)).sum())
    fp = int(((df["expected"] == LABEL_NO_MATCH) & (df["predicted"] == LABEL_MATCH)).sum())
    fn = int(((df["expected"] == LABEL_MATCH) & (df["predicted"] == LABEL_NO_MATCH)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "total": int(len(df)),
        "pass_rate": float((df["status"] == "PASS").mean()),
        "precision_match": float(precision),
        "recall_match": float(recall),
        "f1_match": float(f1),
        "false_match": int((df["error_type"] == "FALSE_MATCH").sum()),
        "false_no_match": int((df["error_type"] == "FALSE_NO_MATCH").sum()),
    }


def style_results(df: pd.DataFrame):
    def row_style(row):
        if row.get("error_type") == "FALSE_MATCH":
            return ["background-color: #fee2e2; color: #7f1d1d"] * len(row)
        if row.get("status") == "FAIL":
            return ["background-color: #fff7ed; color: #7c2d12"] * len(row)
        if row.get("status") == "PASS":
            return ["background-color: #ecfdf5; color: #064e3b"] * len(row)
        return [""] * len(row)

    return df.style.apply(row_style, axis=1).format(
        {
            "p_match": "{:.3f}",
            "p_no_match": "{:.3f}",
            "confidence": "{:.3f}",
            "pass_rate": "{:.1%}",
        }
    )


@st.cache_data(show_spinner=False)
def load_training_dataset(path: str) -> pd.DataFrame:
    dataset_path = Path(path)
    if not dataset_path.exists():
        return pd.DataFrame()
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def read_training_state(model_path: str) -> Dict[str, str]:
    model_dir = Path(model_path)
    search_dir = model_dir.parent if model_dir.name == "final_model" else model_dir
    states = sorted(search_dir.rglob("trainer_state.json"))
    if not states:
        return {}

    best = {}
    final_eval = {}
    selected_state = states[-1]
    for state_path in states:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("best_metric") is not None:
            best = {
                "best_metric": f"{float(state.get('best_metric')):.6f}",
                "best_global_step": str(state.get("best_global_step", "-")),
                "best_model_checkpoint": str(state.get("best_model_checkpoint", "-")),
            }
        for log in state.get("log_history", []):
            if "eval_f1_match" in log:
                final_eval = {
                    "eval_step": str(log.get("step", "-")),
                    "eval_accuracy": f"{float(log.get('eval_accuracy', 0.0)):.6f}",
                    "eval_precision_match": f"{float(log.get('eval_precision_match', 0.0)):.6f}",
                    "eval_recall_match": f"{float(log.get('eval_recall_match', 0.0)):.6f}",
                    "eval_f1_match": f"{float(log.get('eval_f1_match', 0.0)):.6f}",
                }
        selected_state = state_path

    return {
        "trainer_state": str(selected_state),
        **best,
        **final_eval,
    }


def read_json_file(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def checkpoint_step_from_path(path: Path) -> int:
    match = re.search(r"checkpoint-(\d+)", str(path))
    return int(match.group(1)) if match else -1


def latest_trainer_state(training_root: Path) -> tuple[Path | None, Dict]:
    states = sorted(training_root.rglob("trainer_state.json"))
    best_path = None
    best_state: Dict = {}
    best_step = -1
    for state_path in states:
        state = read_json_file(state_path)
        step = int(state.get("global_step") or checkpoint_step_from_path(state_path) or -1)
        if step >= best_step:
            best_step = step
            best_path = state_path
            best_state = state
    return best_path, best_state


def local_checkpoint_for_step(training_root: Path, step_value) -> Path | None:
    step = int(numeric_value(step_value, -1))
    if step < 0:
        return None
    checkpoint = training_root / f"checkpoint-{step}"
    return checkpoint if checkpoint.exists() else None


def trainer_log_frames(state: Dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    history = state.get("log_history", [])
    if not isinstance(history, list):
        return pd.DataFrame(), pd.DataFrame()
    log_df = pd.DataFrame([row for row in history if isinstance(row, dict)])
    if log_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    train_df = log_df[log_df.get("loss").notna()].copy() if "loss" in log_df.columns else pd.DataFrame()
    eval_cols = [col for col in log_df.columns if str(col).startswith("eval_")]
    eval_df = log_df[log_df[eval_cols].notna().any(axis=1)].copy() if eval_cols else pd.DataFrame()
    return train_df, eval_df


def numeric_value(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def best_eval_row(eval_df: pd.DataFrame, preferred_metrics: Sequence[str]) -> tuple[pd.Series | None, str | None]:
    if eval_df.empty:
        return None, None
    for metric in preferred_metrics:
        if metric not in eval_df.columns:
            continue
        values = pd.to_numeric(eval_df[metric], errors="coerce")
        if values.notna().any():
            return eval_df.loc[values.idxmax()], metric
    return eval_df.iloc[-1], None


def format_training_metric(metric_name: str, value) -> str:
    number = numeric_value(value, default=float("nan"))
    if pd.isna(number):
        return "-"
    lower_name = metric_name.lower()
    if "loss" in lower_name:
        return f"{number:.4f}"
    if "runtime" in lower_name:
        return f"{number:.2f} s"
    if "samples_per_second" in lower_name or "steps_per_second" in lower_name:
        return f"{number:.2f}"
    if abs(number) <= 1.5:
        return f"{number * 100:.2f}%"
    return f"{number:.4f}"


def user_metric_label(metric_name: str) -> str:
    labels = {
        "eval_accuracy": "Accuracy",
        "eval_f1": "F1-score",
        "eval_precision": "Precision",
        "eval_recall": "Recall",
        "eval_f1_macro": "F1 macro",
        "eval_precision_macro": "Precision macro",
        "eval_recall_macro": "Recall macro",
        "eval_f1_match": "F1 MATCH",
        "eval_precision_match": "Precision MATCH",
        "eval_recall_match": "Recall MATCH",
        "eval_loss": "Validation loss",
    }
    return labels.get(metric_name, metric_name.replace("eval_", "").replace("_", " ").title())


def config_label_summary(config: Dict) -> str:
    labels = config.get("id2label", {})
    if not isinstance(labels, dict) or not labels:
        return "-"
    ordered = [labels[key] for key in sorted(labels, key=lambda item: int(item) if str(item).isdigit() else str(item))]
    return ", ".join(str(item) for item in ordered)


def compact_path(path: Path | str | None) -> str:
    if not path:
        return "-"
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(ROOT_DIR))
    except Exception:
        return str(path_obj)


def model_report_data(spec: Dict[str, object]) -> Dict[str, object]:
    model_dir = Path(str(spec["model_dir"]))
    training_root = Path(str(spec["training_root"]))
    state_path, state = latest_trainer_state(training_root)
    config = read_json_file(model_dir / "config.json")
    train_df, eval_df = trainer_log_frames(state)
    best_row, best_metric = best_eval_row(eval_df, spec.get("preferred_metrics", []))
    latest_row = eval_df.iloc[-1] if not eval_df.empty else None
    best_checkpoint = (
        local_checkpoint_for_step(training_root, best_row.get("step"))
        if isinstance(best_row, pd.Series)
        else None
    )
    return {
        "spec": spec,
        "config": config,
        "state": state,
        "state_path": state_path,
        "best_checkpoint": best_checkpoint,
        "train_df": train_df,
        "eval_df": eval_df,
        "best_row": best_row,
        "best_metric": best_metric,
        "latest_row": latest_row,
    }


def model_report_summary_row(report: Dict[str, object]) -> Dict[str, str]:
    spec = report["spec"]
    state = report["state"] if isinstance(report["state"], dict) else {}
    best_row = report.get("best_row")
    latest_row = report.get("latest_row")
    primary_metric = str(report.get("best_metric") or "")
    return {
        "Model": str(spec.get("title", "")),
        "Tugas": str(spec.get("task", "")),
        "Checkpoint terbaik": compact_path(report.get("best_checkpoint") or state.get("best_model_checkpoint") or report.get("state_path")),
        "Step terbaik": str(int(numeric_value(best_row.get("step"), 0))) if isinstance(best_row, pd.Series) else "-",
        "Metrik utama": user_metric_label(primary_metric) if primary_metric else "-",
        "Nilai terbaik": format_training_metric(primary_metric, best_row.get(primary_metric)) if isinstance(best_row, pd.Series) and primary_metric else "-",
        "Evaluasi terakhir": format_training_metric(primary_metric, latest_row.get(primary_metric)) if isinstance(latest_row, pd.Series) and primary_metric else "-",
    }


def render_training_metric_cards(report: Dict[str, object]) -> None:
    best_row = report.get("best_row")
    latest_row = report.get("latest_row")
    best_metric = str(report.get("best_metric") or "")
    state = report["state"] if isinstance(report["state"], dict) else {}
    spec = report["spec"]
    metrics = list(spec.get("headline_metrics", []))

    cols = st.columns(5)
    cols[0].metric(
        "Metrik utama terbaik",
        format_training_metric(best_metric, best_row.get(best_metric)) if isinstance(best_row, pd.Series) and best_metric else "-",
        help=user_metric_label(best_metric) if best_metric else None,
    )
    cols[1].metric("Accuracy", format_training_metric("eval_accuracy", best_row.get("eval_accuracy")) if isinstance(best_row, pd.Series) else "-")
    cols[2].metric("F1-score", format_training_metric(metrics[0], best_row.get(metrics[0])) if isinstance(best_row, pd.Series) and metrics else "-")
    recall_metric = next((metric for metric in metrics if "recall" in metric), "")
    precision_metric = next((metric for metric in metrics if "precision" in metric), "")
    cols[3].metric("Precision", format_training_metric(precision_metric, best_row.get(precision_metric)) if isinstance(best_row, pd.Series) and precision_metric else "-")
    cols[4].metric("Recall", format_training_metric(recall_metric, best_row.get(recall_metric)) if isinstance(best_row, pd.Series) and recall_metric else "-")

    detail_cols = st.columns(4)
    detail_cols[0].metric("Epoch", f"{numeric_value(state.get('epoch'), 0):.1f}")
    detail_cols[1].metric("Global step", str(int(numeric_value(state.get("global_step"), 0))))
    detail_cols[2].metric("Train batch", str(state.get("train_batch_size", "-")))
    detail_cols[3].metric(
        "Last eval loss",
        format_training_metric("eval_loss", latest_row.get("eval_loss")) if isinstance(latest_row, pd.Series) else "-",
    )


def render_training_metric_table(report: Dict[str, object]) -> None:
    spec = report["spec"]
    best_row = report.get("best_row")
    latest_row = report.get("latest_row")
    metric_keys = [metric for metric in spec.get("table_metrics", []) if isinstance(metric, str)]
    rows = []
    for metric in metric_keys:
        rows.append(
            {
                "Metrik": user_metric_label(metric),
                "Best validation": format_training_metric(metric, best_row.get(metric)) if isinstance(best_row, pd.Series) else "-",
                "Step best": str(int(numeric_value(best_row.get("step"), 0))) if isinstance(best_row, pd.Series) else "-",
                "Last validation": format_training_metric(metric, latest_row.get(metric)) if isinstance(latest_row, pd.Series) else "-",
                "Step last": str(int(numeric_value(latest_row.get("step"), 0))) if isinstance(latest_row, pd.Series) else "-",
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_training_charts(report: Dict[str, object]) -> None:
    spec = report["spec"]
    train_df = report["train_df"] if isinstance(report["train_df"], pd.DataFrame) else pd.DataFrame()
    eval_df = report["eval_df"] if isinstance(report["eval_df"], pd.DataFrame) else pd.DataFrame()

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("**Training loss**")
        if not train_df.empty and {"step", "loss"}.issubset(train_df.columns):
            chart_df = train_df[["step", "loss"]].copy()
            chart_df["step"] = pd.to_numeric(chart_df["step"], errors="coerce")
            chart_df["loss"] = pd.to_numeric(chart_df["loss"], errors="coerce")
            st.line_chart(chart_df.dropna().set_index("step"), height=260)
        else:
            st.info("Log training loss tidak tersedia.")

    with chart_cols[1]:
        st.markdown("**Validation metric**")
        metric_keys = [metric for metric in spec.get("chart_metrics", []) if metric in eval_df.columns]
        if not eval_df.empty and "step" in eval_df.columns and metric_keys:
            chart_df = eval_df[["step", *metric_keys]].copy()
            chart_df["step"] = pd.to_numeric(chart_df["step"], errors="coerce")
            for metric in metric_keys:
                chart_df[user_metric_label(metric)] = pd.to_numeric(chart_df[metric], errors="coerce")
                chart_df = chart_df.drop(columns=[metric])
            st.line_chart(chart_df.dropna(subset=["step"]).set_index("step"), height=260)
        else:
            st.info("Log metrik validasi tidak tersedia.")

    st.markdown("**Validation loss**")
    if not eval_df.empty and {"step", "eval_loss"}.issubset(eval_df.columns):
        loss_df = eval_df[["step", "eval_loss"]].copy()
        loss_df["step"] = pd.to_numeric(loss_df["step"], errors="coerce")
        loss_df["eval_loss"] = pd.to_numeric(loss_df["eval_loss"], errors="coerce")
        st.line_chart(loss_df.dropna().set_index("step"), height=220)
    else:
        st.info("Validation loss tidak tersedia.")


def render_model_training_report(report: Dict[str, object]) -> None:
    spec = report["spec"]
    config = report["config"] if isinstance(report["config"], dict) else {}
    state = report["state"] if isinstance(report["state"], dict) else {}
    state_path = report.get("state_path")
    model_dir = Path(str(spec["model_dir"]))

    st.markdown(f"### {spec.get('title')}")
    st.caption(str(spec.get("description", "")))
    render_training_metric_cards(report)

    st.markdown("**Metrik evaluasi validasi**")
    render_training_metric_table(report)

    st.markdown("**Grafik training**")
    render_training_charts(report)

    detail_rows = [
        {"Item": "Task", "Nilai": str(spec.get("task", "-"))},
        {"Item": "Base model", "Nilai": str(config.get("_name_or_path") or spec.get("base_model", "-"))},
        {"Item": "Architecture", "Nilai": ", ".join(config.get("architectures", []) or ["-"])},
        {"Item": "Final model", "Nilai": compact_path(model_dir)},
        {"Item": "Trainer state", "Nilai": compact_path(state_path)},
        {"Item": "Best checkpoint", "Nilai": compact_path(report.get("best_checkpoint") or state.get("best_model_checkpoint"))},
        {"Item": "Num labels", "Nilai": str(len(config.get("id2label", {}) or {}))},
        {"Item": "Labels", "Nilai": config_label_summary(config)},
        {"Item": "Max sequence length", "Nilai": str(config.get("max_position_embeddings", "-"))},
        {"Item": "Hidden size / layers", "Nilai": f"{config.get('hidden_size', '-')} / {config.get('num_hidden_layers', '-')}" },
    ]
    st.markdown("**Konfigurasi model yang relevan**")
    st.dataframe(pd.DataFrame(detail_rows), width="stretch", hide_index=True)


def render_model_info_tab() -> None:
    reports = [
        model_report_data(
            {
                "title": "IndoBERT NER",
                "task": "Token classification untuk ekstraksi atribut order",
                "description": "Model ini menandai span atribut seperti tanggal RO, waktu muat, pickup, tujuan, tipe unit, driver, nopol, dan kontak driver.",
                "base_model": "indolem/indobert-base-uncased",
                "model_dir": DEFAULT_NER_MODEL_PATH,
                "training_root": ROOT_DIR / "models" / "indobert_NER",
                "preferred_metrics": ["eval_f1", "eval_accuracy"],
                "headline_metrics": ["eval_f1", "eval_precision", "eval_recall"],
                "table_metrics": ["eval_accuracy", "eval_f1", "eval_precision", "eval_recall", "eval_loss"],
                "chart_metrics": ["eval_f1", "eval_accuracy", "eval_precision", "eval_recall"],
            }
        ),
        model_report_data(
            {
                "title": "IndoBERT SPC",
                "task": "Sequence pair classification untuk pencocokan order lama dan susulan",
                "description": "Model ini memprediksi MATCH atau NO_MATCH dari pasangan state order dan chat susulan.",
                "base_model": "indobenchmark/indobert-base-p2",
                "model_dir": DEFAULT_MODEL_PATH,
                "training_root": ROOT_DIR / "models" / "indobenchmark" / "indobert-base-p2_15k",
                "preferred_metrics": ["eval_f1_match", "eval_f1_macro", "eval_accuracy"],
                "headline_metrics": ["eval_f1_match", "eval_precision_match", "eval_recall_match"],
                "table_metrics": [
                    "eval_accuracy",
                    "eval_f1_macro",
                    "eval_precision_macro",
                    "eval_recall_macro",
                    "eval_f1_match",
                    "eval_precision_match",
                    "eval_recall_match",
                    "eval_loss",
                ],
                "chart_metrics": ["eval_f1_match", "eval_f1_macro", "eval_accuracy"],
            }
        ),
    ]

    st.subheader("Model Info")
    st.caption("Ringkasan pasca-training dari artefak lokal model NER dan SPC.")
    st.dataframe(
        pd.DataFrame([model_report_summary_row(report) for report in reports]),
        width="stretch",
        hide_index=True,
    )

    ner_tab, spc_tab = st.tabs(["IndoBERT NER", "IndoBERT SPC"])
    with ner_tab:
        render_model_training_report(reports[0])
    with spc_tab:
        render_model_training_report(reports[1])


def render_metric_cards(metrics: Dict[str, float | int]) -> None:
    cols = st.columns(6)
    cols[0].metric("Total case", metrics["total"])
    cols[1].metric("Pass rate", f"{metrics['pass_rate']:.1%}")
    cols[2].metric("F1 MATCH", f"{metrics['f1_match']:.1%}")
    cols[3].metric("Precision MATCH", f"{metrics['precision_match']:.1%}")
    cols[4].metric("Recall MATCH", f"{metrics['recall_match']:.1%}")
    cols[5].metric("False MATCH", metrics["false_match"])


def render_case_detail(row: pd.Series) -> None:
    left, right = st.columns(2)
    with left:
        st.text_area("Pesanan awal / order state", row["text_a"], height=280, key=f"a_{row['case_id']}")
    with right:
        st.text_area("Pesanan susulan / incoming", row["text_b"], height=280, key=f"b_{row['case_id']}")

    diag_cols = st.columns(4)
    diag_cols[0].metric("Expected", row["expected"])
    diag_cols[1].metric("Predicted", row["predicted"])
    diag_cols[2].metric("P_MATCH", f"{row['p_match']:.3f}")
    diag_cols[3].metric("Confidence", f"{row['confidence']:.3f}")

    diag = pd.DataFrame(
        [
            {
                "request_date_a": row["request_date_a"],
                "request_date_b": row["request_date_b"],
                "location_a": row["location_a"],
                "location_b": row["location_b"],
                "route_a": row["route_a"],
                "route_b": row["route_b"],
                "unit_type_a": row["unit_type_a"],
                "unit_type_b": row["unit_type_b"],
                "qty_a": row["qty_a"],
                "qty_b": row["qty_b"],
                "incoming_driver_records": row["incoming_driver_records"],
                "rule_advisory": row["rule_advisory"],
            }
        ]
    )
    st.dataframe(diag, width="stretch", hide_index=True)


@st.cache_resource(show_spinner="Loading IndoBERT NER model...")
def load_ner_model(model_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()
    return tokenizer, model, device


def load_default_new_order_sample() -> str:
    if DEFAULT_NEW_ORDER_SAMPLE_PATH.exists():
        return DEFAULT_NEW_ORDER_SAMPLE_PATH.read_text(encoding="utf-8")
    return ""


def split_new_order_messages(raw_text: str) -> List[str]:
    clean = str(raw_text or "").replace("\r", "").lstrip("\ufeff").replace("\ufeff", "")
    clean = clean.strip()
    if not clean:
        return []

    request_header_word = r"(?:requestt?|reqest|reques|requer)"
    header_regex = re.compile(
        r"(?im)^\s*(?:\[[^\]]+\]\s*)?(?:[^:\n]{1,80}:\s*)?"
        rf"(?:{request_header_word}|oncall|unit\s+on\s+call|on\s+call)\b"
    )
    starts = [adjust_chat_header_start(clean, m.start()) for m in header_regex.finditer(clean)]
    starts = sorted(set(starts))
    if not starts:
        return split_multi_unit_order_lines([clean])

    prefix = clean[: starts[0]].strip()
    if starts[0] > 0 and prefix:
        starts = [0] + starts
    starts.append(len(clean))

    chunks = []
    for idx in range(len(starts) - 1):
        chunk = clean[starts[idx] : starts[idx + 1]].strip()
        if chunk:
            chunks.append(chunk)
    return split_multi_unit_order_lines(chunks)


def adjust_chat_header_start(text: str, header_start: int) -> int:
    line_start = text.rfind("\n", 0, header_start) + 1
    if line_start <= 0:
        return header_start

    prev = previous_non_empty_line(text, line_start)
    if not prev:
        return header_start

    prev_start, _, prev_line = prev
    if is_whatsapp_metadata_line(prev_line):
        return prev_start
    return header_start


def previous_non_empty_line(text: str, before_pos: int) -> tuple[int, int, str] | None:
    pos = max(0, before_pos)
    while pos > 0:
        line_end = pos - 1
        while line_end >= 0 and text[line_end] == "\n":
            line_end -= 1
        if line_end < 0:
            return None
        line_start = text.rfind("\n", 0, line_end + 1) + 1
        line = text[line_start : line_end + 1]
        if line.strip():
            return line_start, line_end + 1, line
        pos = line_start
    return None


def is_whatsapp_metadata_line(line: str) -> bool:
    return bool(
        re.match(
            r"^\s*\[\d{1,2}[.,:]\d{2}\s*,\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*",
            str(line or ""),
            re.IGNORECASE,
        )
    )


def split_multi_unit_order_lines(chunks: Sequence[str]) -> List[str]:
    unit_line_regex = re.compile(r"(?im)^\s*\d{1,3}\s*unit\b")
    normalized = []
    for chunk in chunks:
        hits = list(unit_line_regex.finditer(chunk))
        if len(hits) <= 1:
            normalized.append(chunk)
            continue

        header_context = chunk[: hits[0].start()].strip()
        starts = [m.start() for m in hits] + [len(chunk)]
        for idx in range(len(starts) - 1):
            body = chunk[starts[idx] : starts[idx + 1]].strip()
            if not body:
                continue
            normalized.append((header_context + "\n" + body).strip() if header_context else body)
    return normalized


def strip_chat_metadata_for_ner(text: str) -> str:
    cleaned_lines = []
    metadata_prefix = re.compile(
        r"^\s*\[\d{1,2}[.,:]\d{2}\s*,\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*(?:[^:\n]{1,80}:\s*)?",
        re.IGNORECASE,
    )
    metadata_only = re.compile(
        r"^\s*\[\d{1,2}[.,:]\d{2}\s*,\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*$",
        re.IGNORECASE,
    )
    for raw_line in str(text or "").splitlines():
        if metadata_only.match(raw_line):
            continue
        had_metadata = bool(metadata_prefix.match(raw_line))
        line = metadata_prefix.sub("", raw_line).strip()
        if had_metadata and line and not has_ner_content_signal(line):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"(?i)@\s*nomor\s+tidak\s+dikenal", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_ner_field_labels(text: str) -> str:
    """Stabilize noisy WhatsApp field labels without changing extracted values."""
    normalized_lines = []
    replacements = [
        (
            re.compile(r"(?i)^(\s*)lokasi(?:\s*loading|i{1,3})?\s*:\s*"),
            r"\1Lokasi : ",
        ),
        (
            re.compile(r"(?i)^(\s*)waktu\s*(?:loading|loadng|lodng|loding|lodingg|loadingg)\s*:\s*"),
            r"\1Waktu loading : ",
        ),
        (
            re.compile(r"(?i)^(\s*)rute(?:\s*/?\s*(?:tujuan|tujan|tuj|tujuann?))?\s*:\s*"),
            r"\1Rute/tujuan : ",
        ),
        (
            re.compile(r"(?i)^(\s*)(?:d?driver+|drivr|drver|nama)(?:\s*\d+)?\s*:\s*"),
            r"\1Driver : ",
        ),
        (
            re.compile(r"(?i)^(\s*)(?:nopol+|nopl|no\s*pol)\s*:\s*"),
            r"\1Nopol : ",
        ),
        (
            re.compile(r"(?i)^(\s*)(?:no\s*hpp?|nohp|no\s*tlp|no\s*telp|no\s*telepon|kontak)\s*:\s*"),
            r"\1No hp : ",
        ),
    ]

    for raw_line in str(text or "").splitlines():
        line = raw_line
        for pattern, replacement in replacements:
            line = pattern.sub(replacement, line, count=1)
        normalized_lines.append(line)

    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r"(?im)^(\s*)unit\s*/\s*type\s*:\s*", r"\1Unit/Type : ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def is_ner_operational_noise_line(line: str) -> bool:
    stripped = str(line or "").strip()
    if not stripped or ":" in stripped:
        return False
    if re.match(
        r"(?i)^(?:"
        r"fyi\b|info\b|mohon\s+bantu\b|siap\b|yang\b|yg\b|buat\b|data\b|"
        r"unit\s+satu\s+nya\b|noted\b|maaf\b|rafay\b"
        r")",
        stripped,
    ):
        return True
    if re.search(r"(?i)\b(request|order|oncall|on\s+call|tgl|tanggal|\d+\s*unit|lokasi|waktu|rute|driver|nopol|no\s*hp)\b", stripped):
        return False
    return bool(
        re.match(
            r"(?i)^(?:"
            r"mohon\b|pak\b"
            r")",
            stripped,
        )
    )


def remove_ner_operational_noise(text: str) -> str:
    lines = []
    for line in str(text or "").splitlines():
        if is_ner_operational_noise_line(line):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def prepare_text_for_ner(text: str) -> str:
    normalized = normalize_ner_field_labels(strip_chat_metadata_for_ner(text))
    return remove_ner_operational_noise(normalized)




def has_ner_content_signal(line: str) -> bool:
    return bool(
        re.search(
            r"(?i)\b("
            r"requestt?|reqest|reques|requer|order|oncall|on\s+call|unit\s+on\s+call|"
            r"tgl|tanggal|unit|lokasi|loakasi|waktu|loading|rute|tujuan|"
            r"driver|drver|driverr|nama|nopol|nopoll|nopl|no\s*pol|no\s*hp|nohp|"
            r"no\s*tlp|no\s*telp|kontak|unit/type|type"
            r")\b",
            str(line or ""),
        )
    )


def join_wordpiece_tokens(tokens: Sequence[str]) -> str:
    text = ""
    for token in tokens:
        if token.startswith("##"):
            text += token[2:]
        elif token in {".", ",", ":", "/", "-"}:
            text += token
        else:
            if text:
                text += " "
            text += token
    text = re.sub(r"\s+([.,:/-])", r"\1", text)
    text = re.sub(r"([:/-])\s+", r"\1", text)
    return text.strip()


def ner_predict_spans_with_scores(tokenizer, model, device, text: str, max_seq_len: int) -> List[Dict[str, object]]:
    model_input = str(text or "").replace("+62", "0")
    model_max_len = int(getattr(getattr(model, "config", None), "max_position_embeddings", 512) or 512)
    effective_max_len = min(model_max_len, max(int(max_seq_len or 0), 512))
    inputs = tokenizer(
        model_input,
        return_tensors="pt",
        truncation=True,
        max_length=effective_max_len,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0].detach().cpu()
        pred_ids = torch.argmax(probs, dim=-1).tolist()

    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0].detach().cpu().tolist())
    id2label = getattr(model.config, "id2label", {}) or {}
    spans = []
    current_label = ""
    current_tokens: List[str] = []
    current_scores: List[float] = []

    def flush_current() -> None:
        nonlocal current_label, current_tokens, current_scores
        if current_label and current_tokens:
            value = join_wordpiece_tokens(current_tokens)
            if value:
                spans.append(
                    {
                        "label": current_label,
                        "value": value,
                        "confidence": sum(current_scores) / max(1, len(current_scores)),
                    }
                )
        current_label = ""
        current_tokens = []
        current_scores = []

    for idx, (token, pred_id) in enumerate(zip(tokens, pred_ids)):
        if token in {"[CLS]", "[SEP]", "[PAD]"}:
            flush_current()
            continue
        raw_label = str(id2label.get(pred_id) or id2label.get(str(pred_id)) or "O")
        if raw_label == "O" or "-" not in raw_label:
            flush_current()
            continue

        prefix, category = raw_label.split("-", 1)
        score = float(probs[idx, pred_id].item())
        if prefix == "B" or category != current_label:
            flush_current()
            current_label = category
            current_tokens = [token]
            current_scores = [score]
        else:
            current_tokens.append(token)
            current_scores.append(score)

    flush_current()
    return spans


def group_spans(spans: Sequence[Dict[str, object]]) -> Dict[str, List[str]]:
    sequence_labels = {"LOAD_DATE", "TIME", "ORIGIN", "DESTINATION", "DRIVER", "PLATE", "PHONE"}
    grouped: Dict[str, List[str]] = {}
    for span in spans:
        label = str(span.get("label", "")).strip()
        value = clean_cell_value(str(span.get("value", "")))
        if not label or not value:
            continue
        if label == "PHONE" and len(re.sub(r"\D+", "", value)) < 8:
            continue
        grouped.setdefault(label, [])
        if label in sequence_labels or value not in grouped[label]:
            grouped[label].append(value)
    return grouped


def clean_cell_value(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" / ", "/").replace(" - ", "-")
    return value


def first_value(values: Dict[str, List[str]], label: str) -> str:
    return values.get(label, [""])[0] if values.get(label) else ""


def joined_values(values: Dict[str, List[str]], label: str) -> str:
    items = [clean_cell_value(str(item)) for item in values.get(label, []) if filled_value(item)]
    return clean_cell_value(" ".join(items))


def indexed_value(values: Dict[str, List[str]], label: str, idx: int, common: bool = False) -> str:
    items = values.get(label, [])
    if not items:
        return ""
    if common:
        return items[0]
    return items[idx] if idx < len(items) else ""


def common_order_value(values: Dict[str, List[str]], label: str) -> bool:
    items = [clean_cell_value(str(item)) for item in values.get(label, []) if filled_value(item)]
    if len(items) <= 1:
        return True
    normalized = {item.casefold() for item in items}
    return len(normalized) == 1


def qty_from_ner(values: Dict[str, List[str]]) -> int:
    qty_raw = first_value(values, "UNIT_QTY")
    match = re.search(r"\d{1,3}", qty_raw)
    if not match:
        return 1
    qty = int(match.group(0))
    return max(1, min(qty, 80))


def load_text_value(values: Dict[str, List[str]], idx: int) -> str:
    load_dates = values.get("LOAD_DATE", [])
    times = values.get("TIME", [])
    if idx < len(load_dates):
        return load_dates[idx]
    if len(load_dates) == 1:
        return load_dates[0]
    if idx < len(times):
        return times[idx]
    if len(times) == 1:
        return times[0]
    return ""


def loading_values_from_spans(spans: Sequence[Dict[str, object]]) -> List[str]:
    loading_labels = {"TIME", "LOAD_DATE"}
    loading_values: List[str] = []
    idx = 0
    safe_spans = list(spans or [])

    while idx < len(safe_spans):
        label = str(safe_spans[idx].get("label", "")).strip()
        if label not in loading_labels:
            idx += 1
            continue

        parts = []
        while idx < len(safe_spans):
            current_label = str(safe_spans[idx].get("label", "")).strip()
            if current_label not in loading_labels:
                break
            value = clean_cell_value(str(safe_spans[idx].get("value", "")))
            if value:
                parts.append(value)
            idx += 1

        value = clean_cell_value(" ".join(parts))
        if value:
            loading_values.append(value)

    return loading_values


def indexed_loading_value(loading_values: Sequence[str], values: Dict[str, List[str]], idx: int) -> str:
    if idx < len(loading_values):
        return loading_values[idx]
    if len(loading_values) == 1:
        return loading_values[0]
    if loading_values:
        return ""
    return load_text_value(values, idx)


DATE_MONTH_NAMES = {
    1: "JAN",
    2: "FEB",
    3: "MAR",
    4: "APR",
    5: "MEI",
    6: "JUN",
    7: "JUL",
    8: "AGU",
    9: "SEP",
    10: "OKT",
    11: "NOV",
    12: "DES",
}


def canonical_date(value: str) -> str:
    value_raw = str(value or "").strip()
    if not value_raw:
        return ""

    text = stage2_normalize_dates_for_model(value_raw).upper()
    text = re.sub(r"[*.,]+$", "", text.strip())
    month_words = (
        "JANUARI|JAN|FEBRUARI|FEB|MARET|MAR|APRIL|APR|MEI|JUNI|JUN|JULI|JUL|"
        "AGUSTUS|AGU|AUGUST|AUG|SEPTEMBER|SEPT|SEP|OKTOBER|OKT|OCT|NOVEMBER|NOV|"
        "DESEMBER|DES|DEC"
    )

    match = re.search(rf"\b(\d{{1,2}})\s+({month_words})\s+(\d{{2,4}})\b", text)
    if match:
        day = int(match.group(1))
        month_token = match.group(2)
        year = int(match.group(3))
        month_id = month_id_from_token(month_token)
        if month_id:
            if year < 100:
                year += 2000
            return f"{day}-{DATE_MONTH_NAMES[month_id]}-{year}"

    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text)
    if match:
        day = int(match.group(1))
        month_id = int(match.group(2))
        year = int(match.group(3))
        if year < 100:
            year += 2000
        if 1 <= month_id <= 12:
            return f"{day}-{DATE_MONTH_NAMES[month_id]}-{year}"

    return value_raw.upper()


def loading_date_from_rule(raw_loading: str, ro_date: str) -> str:
    ro_canonical = canonical_date(ro_date)
    loading = str(raw_loading or "").strip()
    if not loading:
        return ""

    loading_upper = loading.upper()
    if "SEGERA" in loading_upper:
        return ro_canonical

    specific = canonical_date(loading)
    if specific and specific != loading.upper():
        return specific

    has_time = bool(
        re.search(
            r"\b\d{1,2}\s*[:.;]\s*\d{2}\b|\b\d{1,2}\.\d{2}\b|\b\d{1,2}:\d{2}\b",
            loading_upper,
        )
    )
    if has_time:
        return ro_canonical

    return specific.upper() if specific else loading_upper


def normalize_operational_excel(df: pd.DataFrame) -> pd.DataFrame:
    if not OPERATIONAL_NORMALIZATION_ENABLED:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()

    normalized = df.copy()
    if normalized.empty:
        return normalized

    for idx, row in normalized.iterrows():
        ro_date = canonical_date(str(row.get("Tgl RO", "")))
        raw_loading = str(row.get("_raw_tgl_muat", row.get("Tgl Muat", "")))
        load_date = loading_date_from_rule(raw_loading, ro_date)
        normalized.at[idx, "Tgl RO"] = ro_date
        normalized.at[idx, "Tgl Muat"] = load_date

    for col in EXCEL_COLUMNS:
        if col in normalized.columns:
            normalized[col] = normalized[col].apply(
                lambda value: str(value).upper() if pd.notna(value) else ""
            )
    return normalized


def filled_value(value) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"-", "null", "none", "nan", "undefined"}


def is_sender_name_noise_driver(driver: str, plate: str = "", phone: str = "") -> bool:
    if filled_value(plate) or filled_value(phone):
        return False
    normalized = re.sub(r"\s+", " ", str(driver or "").strip().lower())
    return normalized in {"akbar", "rafay", "akbar rafay"}


_SHORT_NOISE_PICKUP_TOKENS = {"qu", "re", "st"}


def is_short_noise_pickup_token(pickup: str) -> bool:
    token = re.sub(r"[^a-z]", "", str(pickup or "").strip().lower())
    return bool(token) and (token in _SHORT_NOISE_PICKUP_TOKENS or len(token) <= 2)


def should_inherit_previous_pickup_for_empty_unit(
    pickup: str,
    driver: str,
    plate: str,
    phone: str,
) -> bool:
    if any(filled_value(value) for value in (driver, plate, phone)):
        return False
    return is_short_noise_pickup_token(pickup)


def classify_operational_status(row: pd.Series | Dict) -> str:
    fields = [
        "Tgl RO",
        "Tgl Muat",
        "Pickup",
        "Tujuan",
        "No. Plat",
        "Type Truck",
        "Driver",
        "Kontak Driver",
    ]
    filled = sum(1 for field in fields if filled_value(row.get(field, "")))
    if filled >= 8:
        return "ASSIGNED"
    if filled >= 3:
        return "PARTIAL"
    return "UNASSIGNED"


def is_partial_visual_row(row: pd.Series | Dict) -> bool:
    status = str(row.get("status_unit", "") or "").strip().upper()
    if status in {"PARTIAL", "UNASSIGNED"}:
        return True
    return classify_operational_status(row) != "ASSIGNED"


def cell_needs_red_border(row: pd.Series | Dict, col: str) -> bool:
    value = clean_cell_value(str(row.get(col, "") or ""))
    if not value:
        return False
    if col == "Tgl RO":
        return bool(
            re.search(r"(^|\s)-\d{2,4}\b", value)
            or tgl_ro_has_extra_year_issue(value)
        )
    if col == "Tgl Muat":
        return bool(
            re.search(
                r"\b\d{1,2}\s*[:.;]\s*\d{2}\s+\d{1,2}[-/]\d{1,2}\b(?![-/]\d{2,4})",
                value,
            )
        )
    return False


def attr_value_needs_red_border(attribute: str, value: str) -> bool:
    text = clean_cell_value(str(value or ""))
    if not text:
        return False
    if attribute == "Tgl RO":
        return bool(
            re.search(r"(^|\s)-\d{2,4}\b", text)
            or tgl_ro_is_year_only(text)
            or tgl_ro_has_extra_year_issue(text)
        )
    if attribute == "Tgl Muat":
        return bool(
            re.search(
                r"\b\d{1,2}\s*[:.;]\s*\d{2}\s+\d{1,2}[-/]\d{1,2}\b(?![-/]\d{2,4})",
                text,
            )
        )
    return False


def tgl_ro_is_year_only(value: str) -> bool:
    return bool(re.fullmatch(r"(?:19|20)\d{2}", clean_cell_value(value)))


def tgl_ro_has_extra_year_issue(value: str) -> bool:
    text = clean_cell_value(value).casefold()
    month_pattern = (
        r"jan(?:uari|uary)?|feb(?:ruari|ruary|uary)?|mar(?:et|ch)?|"
        r"apr(?:il)?|mei|may|jun(?:i|e)?|jul(?:i|y)?|agu(?:stus)?|"
        r"aug(?:ust)?|sep(?:tember)?|okt(?:ober)?|oct(?:ober)?|"
        r"nov(?:ember)?|des(?:ember)?|dec(?:ember)?"
    )
    return bool(
        re.search(
            rf"\b\d{{1,2}}\s+(?:{month_pattern})\s+((?:19|20)\d{{2}})\s+\1\b",
            text,
        )
    )


def filter_output_by_completion(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if df is None or df.empty or mode == "Semua":
        return df

    mask = df.apply(is_partial_visual_row, axis=1)
    if mode == "Belum lengkap":
        return df[mask].copy()
    if mode == "Lengkap":
        return df[~mask].copy()
    return df


def output_completion_counts(df: pd.DataFrame) -> tuple[int, int, int]:
    if df is None or df.empty:
        return 0, 0, 0
    partial_mask = df.apply(is_partial_visual_row, axis=1)
    total = len(df)
    incomplete = int(partial_mask.sum())
    complete = int(total - incomplete)
    return total, complete, incomplete


def render_output_summary_metrics(df: pd.DataFrame) -> None:
    total, complete, incomplete = output_completion_counts(df)
    metric_cols = st.columns(3)
    metric_cols[0].metric("Total Row", total)
    metric_cols[1].metric("Row Lengkap", complete)
    metric_cols[2].metric("Row Belum Lengkap", incomplete)


def excel_df_to_db_rows(df: pd.DataFrame, job_prefix: str = "") -> List[Dict[str, str]]:
    if df is None or df.empty:
        return []

    rows = []
    safe_df = df.copy().reset_index(drop=True)
    for idx, row in safe_df.iterrows():
        job_number = str(row.get("Job Number", "") or "").strip()
        if not job_number and job_prefix:
            job_number = f"{job_prefix}{idx + 1:04d}"
        rows.append(
            {
                "job_number": job_number,
                "tgl_ro": str(row.get("Tgl RO", "") or "").strip(),
                "tgl_muat": str(row.get("Tgl Muat", "") or "").strip(),
                "pickup": str(row.get("Pickup", "") or "").strip(),
                "tujuan": str(row.get("Tujuan", "") or "").strip(),
                "no_plat": str(row.get("No. Plat", "") or "").strip(),
                "type_truck": str(row.get("Type Truck", "") or "").strip(),
                "driver": str(row.get("Driver", "") or "").strip(),
                "kontak_driver": str(row.get("Kontak Driver", "") or "").strip(),
                "status_unit": str(row.get("status_unit", "") or "").strip()
                or classify_operational_status(row),
            }
        )
    return rows


def db_row_has_operational_payload(row: Dict[str, str]) -> bool:
    return any(
        filled_value(row.get(field, ""))
        for field in (
            "tgl_ro",
            "tgl_muat",
            "pickup",
            "tujuan",
            "no_plat",
            "type_truck",
            "driver",
            "kontak_driver",
        )
    )


def db_rows_to_excel_df(rows: Sequence[Dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])

    mapped = []
    for idx, row in enumerate(rows, start=1):
        mapped.append(
            {
                "No.": idx,
                "Tgl RO": str(row.get("tgl_ro", "") or "").strip(),
                "Tgl Muat": str(row.get("tgl_muat", "") or "").strip(),
                "Pickup": str(row.get("pickup", "") or "").strip(),
                "Tujuan": str(row.get("tujuan", "") or "").strip(),
                "No. Plat": str(row.get("no_plat", "") or "").strip(),
                "Type Truck": str(row.get("type_truck", "") or "").strip(),
                "Driver": str(row.get("driver", "") or "").strip(),
                "Kontak Driver": str(row.get("kontak_driver", "") or "").strip(),
                "status_unit": str(row.get("status_unit", "") or "").strip(),
                "_raw_chat_id": str(row.get("raw_chat_id", "") or "").strip(),
                "_raw_chat_text": str(row.get("raw_chat_text", "") or "").strip(),
            }
        )
    return pd.DataFrame(mapped)


def load_db_excel_df() -> pd.DataFrame:
    if not DB_PERSISTENCE_ENABLED or db_load_all_order_rows is None:
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])
    rows = db_load_all_order_rows()
    return db_rows_to_excel_df(rows)


def load_latest_raw_chat_text_from_db() -> str:
    if not DB_PERSISTENCE_ENABLED or db_load_latest_raw_chat_text is None:
        return ""
    return str(db_load_latest_raw_chat_text() or "").strip()


def load_all_raw_chat_texts_from_db() -> List[str]:
    if not DB_PERSISTENCE_ENABLED or db_load_all_raw_chat_texts is None:
        return []
    return [str(text or "").strip() for text in db_load_all_raw_chat_texts() if str(text or "").strip()]


def load_all_raw_chat_records_from_db() -> List[Dict[str, str]]:
    if not DB_PERSISTENCE_ENABLED or db_load_all_raw_chat_records is None:
        return []
    records = []
    for record in db_load_all_raw_chat_records():
        if not isinstance(record, dict):
            continue
        chat_text = str(record.get("chat_text", "") or "").strip()
        if not chat_text:
            continue
        records.append(
            {
                "id": str(record.get("id", "") or ""),
                "created_at": str(record.get("created_at", "") or ""),
                "chat_text": chat_text,
            }
        )
    return records


def init_operational_db_once() -> bool:
    if not DB_PERSISTENCE_ENABLED or db_init_db is None:
        return False
    if st.session_state.get("ner_db_bootstrap_done"):
        if not st.session_state.get("ner_stage2_schema_bootstrap_done"):
            try:
                db_init_db()
                st.session_state.ner_stage2_schema_bootstrap_done = True
            except Exception:
                pass
        return bool(st.session_state.get("ner_db_ready", False))
    st.session_state.ner_db_bootstrap_done = True
    try:
        st.session_state.ner_db_ready = bool(db_init_db())
        st.session_state.ner_stage2_schema_bootstrap_done = True
    except Exception:
        st.session_state.ner_db_ready = False
    return bool(st.session_state.ner_db_ready)


def sync_extraction_to_db(
    raw_text: str,
    display_df: pd.DataFrame,
    stage2_apply_row: Dict[str, object] | None = None,
    force_distinct_order_save: bool = False,
) -> tuple[pd.DataFrame, str]:
    if (
        not DB_PERSISTENCE_ENABLED
        or db_prepare_chat_for_parsing is None
        or db_save_parsed_rows is None
    ):
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"]), "Database tidak aktif."

    try:
        db_rows = [
            row
            for row in excel_df_to_db_rows(display_df)
            if db_row_has_operational_payload(row)
        ]
        rows_to_save = db_rows
        auto_apply_result: Dict[str, int] = {}
        auto_candidate_key = ""
        if stage2_is_conflict_row(stage2_apply_row):
            reason = str(stage2_apply_row.get("policy_reason", "") or "").strip()
            message = "Stage2 conflict: output ditahan, tidak di-merge dan tidak disimpan sebagai order baru."
            if reason:
                message += f" {reason}"
            return load_db_excel_df(), message

        if not db_rows:
            return load_db_excel_df(), "DB realtime: tidak ada row operasional valid untuk disimpan."

        allow_smart_merge = (
            not force_distinct_order_save
            and not stage2_blocks_smart_merge(stage2_apply_row)
        )
        if stage2_apply_is_ready(stage2_apply_row) and db_apply_stage2_match_fill is not None:
            auto_candidate_key = str(stage2_apply_row.get("candidate_key", "") or "").strip()
            auto_apply_result = db_apply_stage2_match_fill(auto_candidate_key, db_rows)
            filled_count = int(auto_apply_result.get("filled", 0) or 0)
            duplicate_count = int(auto_apply_result.get("duplicates", 0) or 0)
            if filled_count > 0 or duplicate_count > 0:
                rows_to_save = filter_stage2_applied_rows(db_rows, auto_candidate_key)
                stage2_apply_row["auto_applied_count"] = filled_count
                stage2_apply_row["auto_duplicate_count"] = duplicate_count
                stage2_apply_row["action"] = (
                    "AUTO_MERGE_DITERAPKAN" if filled_count > 0 else "ABAIKAN_DUPLIKAT"
                )
                if filled_count > 0:
                    base_reason = str(stage2_apply_row.get("policy_reason", "") or "").strip()
                    stage2_apply_row["policy_reason"] = (
                        f"{base_reason} Auto-merge mengisi {filled_count} slot order lama.".strip()
                    )

        should_parse, raw_chat_id = db_prepare_chat_for_parsing(raw_text)
        if should_parse:
            affected = db_save_parsed_rows(
                raw_chat_id,
                rows_to_save,
                allow_smart_merge=allow_smart_merge,
            )
            message = (
                f"DB realtime: tersimpan sebagai order baru {affected} baris."
                if not allow_smart_merge
                else f"DB realtime: tersimpan/merge {affected} baris."
            )
        else:
            if db_replace_parsed_rows is not None:
                affected = db_replace_parsed_rows(
                    raw_chat_id,
                    rows_to_save,
                    allow_smart_merge=allow_smart_merge,
                )
                message = (
                    f"DB realtime: batch lama direparse, tersimpan sebagai order baru {affected} baris."
                    if not allow_smart_merge
                    else f"DB realtime: batch lama direparse, terganti/merge {affected} baris."
                )
            else:
                message = "DB realtime: batch ini sudah ada, output DB dimuat ulang."

        if auto_apply_result:
            filled_count = int(auto_apply_result.get("filled", 0) or 0)
            duplicate_count = int(auto_apply_result.get("duplicates", 0) or 0)
            skipped_count = int(auto_apply_result.get("skipped", 0) or 0)
            if filled_count > 0:
                message += f" Stage2 auto-merge: {filled_count} slot lama terisi."
            elif duplicate_count > 0:
                message += f" Stage2: {duplicate_count} unit terdeteksi duplikat, tidak disimpan ulang."
            elif auto_candidate_key:
                message += f" Stage2: belum ada slot yang terisi otomatis, {skipped_count} unit dilewati."
        return load_db_excel_df(), message
    except Exception as e:
        return pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"]), f"Gagal sync DB realtime: {e}"


def stage2_norm_key(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        "",
        stage2_normalize_dates_for_model(str(value or "")).strip().lower(),
    )


def stage2_canonical_ro_key(value: str) -> str:
    dates = find_date_tokens(value)
    return dates[0] if dates else ""


def stage2_ro_dates_conflict(left: str, right: str) -> bool:
    left_key = stage2_canonical_ro_key(left)
    right_key = stage2_canonical_ro_key(right)
    return bool(left_key and right_key and left_key != right_key)


def stage2_first_filled(df: pd.DataFrame, col: str) -> str:
    if df is None or df.empty or col not in df.columns:
        return ""
    for value in df[col].tolist():
        text = str(value or "").strip()
        if filled_value(text):
            return text
    return ""


def stage2_unit_payload(row: pd.Series | Dict) -> str:
    parts = [
        str(row.get("Tgl Muat", "") or "").strip(),
        str(row.get("Driver", "") or "").strip(),
        str(row.get("No. Plat", "") or "").strip(),
        str(row.get("Kontak Driver", "") or "").strip(),
    ]
    return " ".join(part for part in parts if filled_value(part)).strip()


def stage2_identity_tokens(row: pd.Series | Dict) -> List[str]:
    tokens = []
    for col in ("No. Plat", "Kontak Driver", "Driver"):
        value = stage2_norm_key(str(row.get(col, "") or ""))
        if value:
            tokens.append(f"{col}:{value}")
    return tokens


def stage2_identity_signature(row: pd.Series | Dict) -> Dict[str, str]:
    return {
        "driver": stage2_norm_key(str(row.get("Driver", row.get("driver", "")) or "")),
        "no_plat": stage2_norm_key(str(row.get("No. Plat", row.get("no_plat", "")) or "")),
        "kontak_driver": stage2_norm_key(
            str(row.get("Kontak Driver", row.get("kontak_driver", "")) or "")
        ),
    }


def stage2_identity_is_duplicate(existing: Dict[str, str], incoming: Dict[str, str]) -> bool:
    # Plat kendaraan adalah identitas unit paling stabil. Phone saja tidak cukup
    # karena NER bisa bergeser pada nomor HP berurutan.
    if existing.get("no_plat") and incoming.get("no_plat") and existing["no_plat"] == incoming["no_plat"]:
        return True

    same_fields = 0
    for field in ("driver", "no_plat", "kontak_driver"):
        if existing.get(field) and incoming.get(field) and existing[field] == incoming[field]:
            same_fields += 1
    return same_fields >= 2


def stage2_has_duplicate_unit(existing_rows: Sequence[Dict], incoming_row: Dict) -> bool:
    incoming_signature = stage2_identity_signature(incoming_row)
    return any(
        stage2_identity_is_duplicate(stage2_identity_signature(existing_row), incoming_signature)
        for existing_row in existing_rows
    )


def stage2_has_complete_identity(row: pd.Series | Dict) -> bool:
    return all(
        filled_value(str(row.get(col, "") or ""))
        for col in ("Driver", "No. Plat", "Kontak Driver")
    )


def stage2_complete_unit_rows(df: pd.DataFrame) -> List[Dict[str, str]]:
    if df is None or df.empty:
        return []
    rows = []
    for _, row in df.iterrows():
        if not stage2_has_complete_identity(row):
            continue
        rows.append(
            {
                "driver": str(row.get("Driver", "") or "").strip(),
                "no_plat": str(row.get("No. Plat", "") or "").strip(),
                "kontak_driver": str(row.get("Kontak Driver", "") or "").strip(),
                "tgl_muat": str(row.get("Tgl Muat", "") or "").strip(),
                "tokens": stage2_identity_tokens(row),
            }
        )
    return rows


def stage2_snapshot_row(row: pd.Series | Dict, marker: str = "") -> Dict[str, str]:
    payload = {
        col: str(row.get(col, "") or "").strip()
        for col in EXCEL_COLUMNS
        if col != "No."
    }
    complete = all(
        filled_value(payload.get(col, ""))
        for col in ("Driver", "No. Plat", "Kontak Driver")
    )
    if marker:
        status = marker
    elif complete:
        status = "TERISI"
    else:
        status = "SLOT KOSONG"
    payload["Status"] = status
    payload["_marker"] = marker
    return payload


def stage2_snapshot_rows_from_df(df: pd.DataFrame) -> List[Dict[str, str]]:
    if df is None or df.empty:
        return []
    return [stage2_snapshot_row(row) for _, row in df.iterrows()]


def stage2_new_incoming_snapshot_rows(
    incoming_df: pd.DataFrame,
    candidate_existing_rows: Sequence[Dict],
) -> List[Dict[str, str]]:
    if incoming_df is None or incoming_df.empty:
        return []

    rows: List[Dict[str, str]] = []
    for _, row in incoming_df.iterrows():
        if not stage2_has_complete_identity(row):
            continue
        if stage2_has_duplicate_unit(candidate_existing_rows, row.to_dict()):
            continue
        rows.append(stage2_snapshot_row(row, marker="BARU"))
    return rows


def stage2_row_value(row: pd.Series | Dict, col: str) -> str:
    return str(row.get(col, "") or "").strip()


def stage2_values_differ(left: str, right: str) -> bool:
    return bool(filled_value(left) and filled_value(right) and stage2_norm_key(left) != stage2_norm_key(right))


def stage2_incoming_snapshot_rows(incoming_df: pd.DataFrame) -> List[Dict[str, str]]:
    if incoming_df is None or incoming_df.empty:
        return []
    return [stage2_snapshot_row(row) for _, row in incoming_df.iterrows()]


def stage2_match_registered_units(
    existing_rows: Sequence[Dict[str, str]],
    incoming_rows: Sequence[Dict[str, str]],
) -> List[Dict[str, object]]:
    matches: List[Dict[str, object]] = []
    used_incoming: set[int] = set()
    existing_complete = [
        row for row in existing_rows if stage2_snapshot_identity_complete(row)
    ]
    incoming_complete = [
        (idx, row)
        for idx, row in enumerate(incoming_rows)
        if stage2_snapshot_identity_complete(row)
    ]

    for existing in existing_complete:
        best_idx = -1
        best_row: Dict[str, str] | None = None
        best_score = 0
        best_same: Dict[str, bool] = {}
        existing_sig = stage2_identity_signature(existing)

        for idx, incoming in incoming_complete:
            if idx in used_incoming:
                continue
            incoming_sig = stage2_identity_signature(incoming)
            same = {
                "driver": bool(existing_sig.get("driver") and existing_sig.get("driver") == incoming_sig.get("driver")),
                "no_plat": bool(existing_sig.get("no_plat") and existing_sig.get("no_plat") == incoming_sig.get("no_plat")),
                "kontak_driver": bool(
                    existing_sig.get("kontak_driver")
                    and existing_sig.get("kontak_driver") == incoming_sig.get("kontak_driver")
                ),
            }
            score = (
                (4 if same["no_plat"] else 0)
                + (3 if same["kontak_driver"] else 0)
                + (2 if same["driver"] else 0)
            )
            if score > best_score:
                best_score = score
                best_idx = idx
                best_row = incoming
                best_same = same

        if best_row is not None and best_score > 0:
            used_incoming.add(best_idx)
            matches.append(
                {
                    "existing": existing,
                    "incoming": best_row,
                    "same": best_same,
                    "score": best_score,
                }
            )

    return matches


def stage2_detect_candidate_conflicts(
    candidate: Stage2OrderCandidate,
    incoming_df: pd.DataFrame,
) -> List[str]:
    incoming_rows = stage2_incoming_snapshot_rows(incoming_df)
    registered_matches = stage2_match_registered_units(candidate.snapshot_rows, incoming_rows)

    conflicts: List[str] = []
    incoming_tgl_ro = stage2_first_filled(incoming_df, "Tgl RO")
    incoming_pickup = stage2_first_filled(incoming_df, "Pickup")
    incoming_tujuan = stage2_first_filled(incoming_df, "Tujuan")
    incoming_type = stage2_first_filled(incoming_df, "Type Truck")
    incoming_qty = len(incoming_df.index) if incoming_df is not None and not incoming_df.empty else 0
    existing_registered_units = [
        row for row in candidate.snapshot_rows if stage2_snapshot_identity_complete(row)
    ]
    incoming_complete_rows = [
        row for row in incoming_rows if stage2_snapshot_identity_complete(row)
    ]
    same_order_context = (
        not stage2_ro_dates_conflict(candidate.tgl_ro, incoming_tgl_ro)
        and not stage2_values_differ(candidate.pickup, incoming_pickup)
        and not stage2_values_differ(candidate.tujuan, incoming_tujuan)
        and not stage2_values_differ(candidate.type_truck, incoming_type)
        and bool(incoming_qty and incoming_qty == int(candidate.qty_target))
    )

    if (
        not registered_matches
        and same_order_context
        and int(candidate.empty or 0) > 0
        and existing_registered_units
        and incoming_complete_rows
    ):
        conflicts.append(
            "Chat susulan tidak mengulang unit lama yang sudah terdaftar; auto-merge ditahan."
        )

    if not registered_matches:
        return list(dict.fromkeys(conflicts))

    # Tgl RO berbeda tetap diperlakukan sebagai order baru jelas, bukan conflict.
    if not stage2_ro_dates_conflict(candidate.tgl_ro, incoming_tgl_ro):
        if stage2_values_differ(candidate.pickup, incoming_pickup):
            conflicts.append("Lokasi pickup berubah pada chat yang membawa unit lama.")
        if stage2_values_differ(candidate.tujuan, incoming_tujuan):
            conflicts.append("Rute/tujuan berubah pada chat yang membawa unit lama.")
        if stage2_values_differ(candidate.type_truck, incoming_type):
            conflicts.append("Tipe unit berubah pada chat yang membawa unit lama.")
        if incoming_qty and incoming_qty != int(candidate.qty_target):
            conflicts.append("Jumlah unit berubah pada chat yang membawa unit lama.")

    for match in registered_matches:
        existing = match["existing"]
        incoming = match["incoming"]
        same = match["same"]
        if not stage2_ro_dates_conflict(candidate.tgl_ro, incoming_tgl_ro):
            if stage2_values_differ(
                stage2_row_value(existing, "Pickup") or candidate.pickup,
                stage2_row_value(incoming, "Pickup"),
            ):
                conflicts.append("Lokasi pickup berubah pada unit lama yang terdaftar.")
            if stage2_values_differ(
                stage2_row_value(existing, "Tujuan") or candidate.tujuan,
                stage2_row_value(incoming, "Tujuan"),
            ):
                conflicts.append("Rute/tujuan berubah pada unit lama yang terdaftar.")
            if stage2_values_differ(
                stage2_row_value(existing, "Type Truck") or candidate.type_truck,
                stage2_row_value(incoming, "Type Truck"),
            ):
                conflicts.append("Tipe unit berubah pada unit lama yang terdaftar.")
        if (
            (same.get("no_plat") or same.get("kontak_driver"))
            and stage2_values_differ(
                stage2_row_value(existing, "Driver"),
                stage2_row_value(incoming, "Driver"),
            )
        ):
            conflicts.append("Nama driver berubah untuk unit yang sudah terdaftar.")
        if (
            (same.get("driver") or same.get("kontak_driver"))
            and stage2_values_differ(
                stage2_row_value(existing, "No. Plat"),
                stage2_row_value(incoming, "No. Plat"),
            )
        ):
            conflicts.append("No. plat berubah untuk unit yang sudah terdaftar.")
        if (
            (same.get("driver") or same.get("no_plat"))
            and stage2_values_differ(
                stage2_row_value(existing, "Kontak Driver"),
                stage2_row_value(incoming, "Kontak Driver"),
            )
        ):
            conflicts.append("Kontak driver berubah untuk unit yang sudah terdaftar.")
        if stage2_values_differ(
            stage2_row_value(existing, "Tgl Muat"),
            stage2_row_value(incoming, "Tgl Muat"),
        ):
            conflicts.append("Waktu loading berubah untuk unit yang sudah terdaftar.")

    return list(dict.fromkeys(conflicts))


def stage2_snapshot_identity_complete(row: Dict[str, str]) -> bool:
    return all(
        filled_value(row.get(col, ""))
        for col in ("Driver", "No. Plat", "Kontak Driver")
    )


def stage2_simulate_after_snapshot(
    candidate: Stage2OrderCandidate,
    incoming_df: pd.DataFrame,
) -> List[Dict[str, str]]:
    after_rows = [dict(row) for row in candidate.snapshot_rows]
    if not after_rows:
        return []

    incoming_new_rows = stage2_new_incoming_snapshot_rows(
        incoming_df,
        candidate.snapshot_rows,
    )
    if not incoming_new_rows:
        return after_rows

    target_indexes = [
        idx
        for idx, row in enumerate(after_rows)
        if not stage2_snapshot_identity_complete(row)
    ]

    for target_idx, incoming_row in zip(target_indexes, incoming_new_rows):
        target = after_rows[target_idx]
        for col in EXCEL_COLUMNS:
            if col == "No.":
                continue
            incoming_value = str(incoming_row.get(col, "") or "").strip()
            if filled_value(incoming_value):
                target[col] = incoming_value
        target["Status"] = "BARU"
        target["_marker"] = "BARU"
    return after_rows


def stage2_plan_for_candidate(
    candidate: Stage2OrderCandidate,
    incoming_df: pd.DataFrame,
    p_match: float,
    predicted_label: str,
) -> Dict[str, object]:
    incoming_units = stage2_complete_unit_rows(incoming_df)
    incoming_tgl_ro = stage2_first_filled(incoming_df, "Tgl RO")
    date_conflict = stage2_ro_dates_conflict(candidate.tgl_ro, incoming_tgl_ro)
    conflict_reasons = stage2_detect_candidate_conflicts(candidate, incoming_df)
    duplicate_units = 0
    new_units = 0
    for unit in incoming_units:
        if stage2_has_duplicate_unit(candidate.snapshot_rows, unit):
            duplicate_units += 1
        else:
            new_units += 1

    proposed_fill_count = min(new_units, max(0, int(candidate.empty)))
    overflow_units = max(0, new_units - max(0, int(candidate.empty)))
    p_match = float(p_match or 0.0)
    predicted_label = str(predicted_label or "")

    if date_conflict:
        decision_status = "TIDAK_COCOK"
        action = "SIMPAN_SEBAGAI_ORDER_BARU"
        reason = "Tgl RO berbeda setelah normalisasi nama bulan; merge diblokir oleh aturan bisnis."
        review_required = False
    elif not incoming_units:
        decision_status = "PERLU_REVIEW"
        action = "CHAT_TIDAK_MEMBAWA_UNIT_LENGKAP"
        reason = "NER belum menghasilkan unit lengkap dari chat masuk."
        review_required = True
    elif new_units <= 0 and duplicate_units > 0:
        decision_status = "DUPLIKAT"
        action = "ABAIKAN_DUPLIKAT"
        reason = "Identitas unit di chat masuk sudah ada pada order kandidat."
        review_required = False
    elif (
        predicted_label == LABEL_NO_MATCH
        and p_match < STAGE2_CLEAR_NEW_ORDER_MAX_MATCH
        and duplicate_units == 0
    ):
        decision_status = "TIDAK_COCOK"
        action = "SIMPAN_SEBAGAI_ORDER_BARU"
        reason = (
            "Score matcher sangat rendah; chat diperlakukan sebagai order baru "
            "sebelum rule conflict diterapkan."
        )
        review_required = False
    elif conflict_reasons:
        decision_status = STAGE2_STATUS_CONFLICT
        action = "TAHAN_AUDIT_CONFLICT"
        reason = " ".join(conflict_reasons)
        review_required = True
    elif predicted_label != LABEL_MATCH or p_match < STAGE2_REVIEW_MATCH_THRESHOLD:
        decision_status = "TIDAK_COCOK"
        action = "SIMPAN_SEBAGAI_ORDER_BARU"
        reason = "Score matcher di bawah ambang review atau model memprediksi NO_MATCH."
        review_required = False
    elif p_match >= STAGE2_STRONG_MATCH_THRESHOLD and proposed_fill_count > 0 and overflow_units == 0:
        decision_status = "SIAP_ISI_SLOT"
        action = "REKOMENDASI_ISI_SLOT_ORDER_LAMA"
        reason = "Score tinggi, ada unit baru lengkap, dan jumlah unit tidak melebihi sisa slot."
        review_required = False
    else:
        decision_status = "PERLU_REVIEW"
        action = "REVIEW_MANUAL"
        if overflow_units > 0:
            reason = "Unit baru lebih banyak dari sisa slot order kandidat."
        elif proposed_fill_count <= 0:
            reason = "Tidak ada slot yang bisa diisi dari unit baru."
        else:
            reason = "Score masuk area review, belum cukup aman untuk auto-fill."
        review_required = True

    return {
        "decision_status": decision_status,
        "action": action,
        "policy_reason": reason,
        "incoming_complete_units": len(incoming_units),
        "duplicate_units": duplicate_units,
        "new_units": new_units,
        "proposed_fill_count": proposed_fill_count,
        "overflow_units": overflow_units,
        "review_required": review_required,
        "date_conflict": date_conflict,
        "conflict_reasons": conflict_reasons,
        "candidate_tgl_ro_key": stage2_canonical_ro_key(candidate.tgl_ro),
        "incoming_tgl_ro_key": stage2_canonical_ro_key(incoming_tgl_ro),
    }


def build_stage2_order_candidates(order_df: pd.DataFrame) -> List[Stage2OrderCandidate]:
    if order_df is None or order_df.empty:
        return []

    safe_df = order_df.copy().reset_index(drop=True)
    for col in EXCEL_COLUMNS + ["status_unit", "_raw_chat_text"]:
        if col not in safe_df.columns:
            safe_df[col] = ""

    group_map: Dict[str, List[int]] = {}
    for idx, row in safe_df.iterrows():
        key_parts = [
            stage2_norm_key(row.get("Tgl RO", "")),
            stage2_norm_key(row.get("Pickup", "")),
            stage2_norm_key(row.get("Tujuan", "")),
            stage2_norm_key(row.get("Type Truck", "")),
        ]
        if not any(key_parts):
            continue
        group_key = "|".join(key_parts)
        group_map.setdefault(group_key, []).append(idx)

    candidates: List[Stage2OrderCandidate] = []
    for group_key, indexes in group_map.items():
        group = safe_df.loc[indexes].copy()
        qty_target = len(group)
        if qty_target <= 0:
            continue

        incomplete_mask = group.apply(is_partial_visual_row, axis=1)
        empty = int(incomplete_mask.sum())
        filled = int(qty_target - empty)
        if empty <= 0:
            continue

        tgl_ro = stage2_first_filled(group, "Tgl RO")
        pickup = stage2_first_filled(group, "Pickup")
        tujuan = stage2_first_filled(group, "Tujuan")
        type_truck = stage2_first_filled(group, "Type Truck")
        source_chat_text = stage2_first_filled(group, "_raw_chat_text")
        snapshot_rows = tuple(stage2_snapshot_rows_from_df(group))
        if filled_value(source_chat_text):
            source_mask = group["_raw_chat_text"].astype(str).str.strip() == source_chat_text
            source_group = group.loc[source_mask].copy()
            if source_group.empty:
                source_group = group.copy()
        else:
            source_group = group.copy()
        source_chat_rows = tuple(stage2_snapshot_rows_from_df(source_group))
        units = [
            stage2_unit_payload(row)
            for _, row in group.iterrows()
            if stage2_unit_payload(row)
        ]
        identity_keys = tuple(
            token
            for _, row in group.iterrows()
            for token in stage2_identity_tokens(row)
        )
        unit_summary = " ; ".join(units) if units else "-"
        text_a = (
            f"ORDER_STATE | Tanggal request: {tgl_ro} | Qty target: {qty_target} | "
            f"Terisi: {filled}/{qty_target} | Sisa slot: {empty} | Unit: {type_truck} | "
            f"Lokasi: {pickup} | Rute/tujuan: {tujuan} | Unit terdata: {unit_summary}"
        )
        summary = (
            f"{tgl_ro or '-'} | {pickup or '-'} | {tujuan or '-'} | "
            f"{type_truck or '-'} | terisi {filled}/{qty_target}"
        )
        candidates.append(
            Stage2OrderCandidate(
                candidate_key=group_key,
                summary=summary,
                text_a=clean_text(text_a),
                qty_target=qty_target,
                filled=filled,
                empty=empty,
                pickup=pickup,
                tujuan=tujuan,
                type_truck=type_truck,
                tgl_ro=tgl_ro,
                identity_keys=identity_keys,
                source_chat_text=source_chat_text,
                source_chat_rows=source_chat_rows,
                snapshot_rows=snapshot_rows,
            )
        )

    return candidates


def stage2_candidate_context_score(candidate: Stage2OrderCandidate, incoming_df: pd.DataFrame) -> int:
    if incoming_df is None or incoming_df.empty:
        return 0
    checks = [
        (candidate.tgl_ro, stage2_first_filled(incoming_df, "Tgl RO"), 2),
        (candidate.pickup, stage2_first_filled(incoming_df, "Pickup"), 3),
        (candidate.tujuan, stage2_first_filled(incoming_df, "Tujuan"), 3),
        (candidate.type_truck, stage2_first_filled(incoming_df, "Type Truck"), 2),
    ]
    score = 0
    for left, right, weight in checks:
        if not filled_value(left) or not filled_value(right):
            continue
        score += weight if stage2_norm_key(left) == stage2_norm_key(right) else -weight
    return score


def build_stage2_match_preview(
    existing_order_df: pd.DataFrame,
    incoming_raw_text: str,
    incoming_df: pd.DataFrame,
    tokenizer,
    model,
    device,
    max_seq_len: int,
    threshold: float,
    batch_size: int,
    top_k: int = 8,
) -> List[Dict[str, object]]:
    incoming_text = clean_text(incoming_raw_text)
    if not incoming_text:
        return []

    candidates = build_stage2_order_candidates(existing_order_df)
    if not candidates:
        return []

    ranked_candidates = sorted(
        candidates,
        key=lambda item: stage2_candidate_context_score(item, incoming_df),
        reverse=True,
    )[: max(1, int(top_k))]
    pairs = [(candidate.text_a, incoming_text) for candidate in ranked_candidates]
    predictions = predict_pairs(
        tokenizer,
        model,
        device,
        pairs,
        max_seq_len=max_seq_len,
        threshold=threshold,
        batch_size=batch_size,
    )

    rows: List[Dict[str, object]] = []
    for candidate, pred in zip(ranked_candidates, predictions):
        predicted = str(pred.get("predicted", "") or "")
        p_match = float(pred.get("p_match", 0.0) or 0.0)
        plan = stage2_plan_for_candidate(candidate, incoming_df, p_match, predicted)
        rows.append(
            {
                "candidate_key": candidate.candidate_key,
                "candidate_summary": candidate.summary,
                "qty_target": candidate.qty_target,
                "filled": candidate.filled,
                "empty": candidate.empty,
                "predicted_label": predicted,
                "p_match": p_match,
                "p_no_match": float(pred.get("p_no_match", max(0.0, 1.0 - p_match)) or 0.0),
                "confidence": float(pred.get("confidence", 0.0) or 0.0),
                "action": str(plan.get("action", "")),
                "decision_status": str(plan.get("decision_status", "")),
                "policy_reason": str(plan.get("policy_reason", "")),
                "incoming_complete_units": int(plan.get("incoming_complete_units", 0) or 0),
                "duplicate_units": int(plan.get("duplicate_units", 0) or 0),
                "new_units": int(plan.get("new_units", 0) or 0),
                "proposed_fill_count": int(plan.get("proposed_fill_count", 0) or 0),
                "overflow_units": int(plan.get("overflow_units", 0) or 0),
                "review_required": bool(plan.get("review_required", False)),
                "date_conflict": bool(plan.get("date_conflict", False)),
                "conflict_reasons": list(plan.get("conflict_reasons", []) or []),
                "candidate_tgl_ro_key": str(plan.get("candidate_tgl_ro_key", "") or ""),
                "incoming_tgl_ro_key": str(plan.get("incoming_tgl_ro_key", "") or ""),
                "order_state_text": candidate.text_a,
                "candidate_chat_text": candidate.source_chat_text,
                "candidate_source_rows": [dict(row) for row in candidate.source_chat_rows],
                "incoming_text": incoming_text,
                "incoming_rows": stage2_snapshot_rows_from_df(incoming_df),
                "before_rows": [dict(row) for row in candidate.snapshot_rows],
                "after_rows": stage2_simulate_after_snapshot(candidate, incoming_df),
            }
        )

    def preview_sort_key(row: Dict[str, object]) -> tuple[int, int, float]:
        status = str(row.get("decision_status", "") or "")
        conflict = 1 if status == STAGE2_STATUS_CONFLICT else 0
        actionable = 1 if status == "SIAP_ISI_SLOT" else 0
        date_ok = 0 if bool(row.get("date_conflict", False)) else 1
        return (conflict, actionable, date_ok, float(row.get("p_match", 0.0) or 0.0))

    return sorted(rows, key=preview_sort_key, reverse=True)


def save_stage2_match_preview(raw_text: str, preview_rows: Sequence[Dict[str, object]]) -> int:
    if (
        not DB_PERSISTENCE_ENABLED
        or db_save_stage2_match_audits is None
        or db_find_raw_chat_id is None
        or not preview_rows
    ):
        return 0
    raw_chat_id = db_find_raw_chat_id(raw_text)
    audit_rows = []
    for row in preview_rows[:STAGE2_AUDIT_SAVE_LIMIT]:
        safe_row = dict(row)
        candidate_chat_text = resolve_stage2_candidate_chat_text(safe_row)
        if candidate_chat_text:
            safe_row["candidate_chat_text"] = candidate_chat_text
            safe_row["order_state_text"] = candidate_chat_text
        audit_rows.append(safe_row)
    return int(db_save_stage2_match_audits(raw_chat_id, audit_rows) or 0)


def stage2_apply_is_ready(row: Dict[str, object] | None) -> bool:
    if not isinstance(row, dict):
        return False
    return (
        str(row.get("decision_status", "") or "") == "SIAP_ISI_SLOT"
        and int(row.get("proposed_fill_count", 0) or 0) > 0
        and int(row.get("overflow_units", 0) or 0) <= 0
        and not bool(row.get("review_required", False))
        and str(row.get("candidate_key", "") or "").strip() != ""
    )


def stage2_is_conflict_row(row: Dict[str, object] | None) -> bool:
    if not isinstance(row, dict):
        return False
    status = str(row.get("decision_status", "") or "").strip().upper()
    action = str(row.get("action", "") or "").strip().upper()
    return status == STAGE2_STATUS_CONFLICT or action == "TAHAN_AUDIT_CONFLICT"


def stage2_blocks_smart_merge(row: Dict[str, object] | None) -> bool:
    if not isinstance(row, dict):
        return False
    status = str(row.get("decision_status", "") or "").strip().upper()
    action = str(row.get("action", "") or "").strip().upper()
    predicted_label = str(row.get("predicted_label", "") or "").strip().upper()
    return (
        status == "TIDAK_COCOK"
        or status == STAGE2_STATUS_CONFLICT
        or action == "SIMPAN_SEBAGAI_ORDER_BARU"
        or action == "TAHAN_AUDIT_CONFLICT"
        or predicted_label == LABEL_NO_MATCH
    )


def stage2_db_row_candidate_key(row: Dict[str, str]) -> str:
    return "|".join(
        [
            stage2_norm_key(row.get("tgl_ro", row.get("Tgl RO", ""))),
            stage2_norm_key(row.get("pickup", row.get("Pickup", ""))),
            stage2_norm_key(row.get("tujuan", row.get("Tujuan", ""))),
            stage2_norm_key(row.get("type_truck", row.get("Type Truck", ""))),
        ]
    )


def stage2_is_order_state_text(text: str) -> bool:
    return str(text or "").strip().upper().startswith("ORDER_STATE")


def find_stage2_candidate_raw_chat_text(candidate_key: str) -> str:
    candidate_key = str(candidate_key or "").strip()
    if not candidate_key:
        return ""

    db_df = load_db_excel_df()
    if db_df is None or db_df.empty or "_raw_chat_text" not in db_df.columns:
        return ""

    for _, row in db_df.iterrows():
        row_dict = row.to_dict()
        if stage2_db_row_candidate_key(row_dict) != candidate_key:
            continue
        raw_text = str(row_dict.get("_raw_chat_text", "") or "").strip()
        if filled_value(raw_text) and not stage2_is_order_state_text(raw_text):
            return raw_text
    return ""


def resolve_stage2_candidate_chat_text(row: Dict[str, object]) -> str:
    candidate_text = str(row.get("candidate_chat_text", "") or "").strip()
    if filled_value(candidate_text) and not stage2_is_order_state_text(candidate_text):
        return candidate_text

    order_state_text = str(row.get("order_state_text", "") or "").strip()
    if filled_value(order_state_text) and not stage2_is_order_state_text(order_state_text):
        return order_state_text

    return find_stage2_candidate_raw_chat_text(str(row.get("candidate_key", "") or ""))


def filter_stage2_applied_rows(rows: Sequence[Dict[str, str]], candidate_key: str) -> List[Dict[str, str]]:
    candidate_key = str(candidate_key or "").strip()
    if not candidate_key:
        return list(rows)
    return [
        row
        for row in rows
        if stage2_db_row_candidate_key(row) != candidate_key
    ]


def sync_extraction_blocks_sequentially(
    raw_text: str,
    ner_tokenizer,
    ner_model,
    ner_device,
    ner_max_seq_len: int,
    matcher_tokenizer,
    matcher_model,
    matcher_device,
    matcher_max_seq_len: int,
    matcher_threshold: float,
    matcher_batch_size: int,
) -> tuple[pd.DataFrame, str, List[Dict[str, object]]]:
    """
    Jalur khusus input multi-blok: setiap blok chat disimpan/di-merge berurutan.

    Ini membuat blok kedua di paste yang sama bisa melihat blok pertama yang baru
    masuk DB, tanpa mengubah jalur single-chat yang sudah stabil.
    """
    chunks = split_new_order_messages(raw_text)
    if len(chunks) <= 1:
        return (
            pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"]),
            "Intra-batch tidak aktif karena input hanya satu blok.",
            [],
        )

    last_preview_rows: List[Dict[str, object]] = []
    messages: List[str] = []
    processed = 0
    for chunk_index, chunk in enumerate(chunks, start=1):
        chunk_df, _ = rows_from_new_order_text(
            ner_tokenizer,
            ner_model,
            ner_device,
            chunk,
            int(ner_max_seq_len),
        )
        if chunk_df.empty:
            messages.append(f"Blok {chunk_index}: tidak ada output NER.")
            continue

        existing_df = load_db_excel_df()
        preview_rows: List[Dict[str, object]] = []
        if not existing_df.empty:
            preview_rows = build_stage2_match_preview(
                existing_df,
                chunk,
                chunk_df,
                matcher_tokenizer,
                matcher_model,
                matcher_device,
                max_seq_len=int(matcher_max_seq_len),
                threshold=float(matcher_threshold),
                batch_size=int(matcher_batch_size),
            )

        stage2_apply_row = preview_rows[0] if preview_rows else None
        # Pada paste multi-blok, order baru yang mirip tidak boleh dilipat oleh
        # smart-merge DB kecuali Stage2 sudah eksplisit menyatakan siap isi slot.
        force_distinct_order_save = not stage2_apply_is_ready(stage2_apply_row)
        _, db_message = sync_extraction_to_db(
            chunk,
            chunk_df,
            stage2_apply_row,
            force_distinct_order_save=force_distinct_order_save,
        )
        processed += 1
        messages.append(f"Blok {chunk_index}: {db_message}")

        if preview_rows:
            last_preview_rows = preview_rows
            try:
                save_stage2_match_preview(chunk, preview_rows)
            except Exception:
                pass

    final_df = load_db_excel_df()
    summary = f"Intra-batch sequential: {processed}/{len(chunks)} blok diproses."
    if messages:
        summary = f"{summary} " + " ".join(messages[-3:])
    return final_df, summary, last_preview_rows


def stage2_operational_decision(row: Dict[str, object]) -> Dict[str, str]:
    status = str(row.get("decision_status", "") or "")
    action = str(row.get("action", "") or "")
    auto_applied = int(row.get("auto_applied_count", 0) or 0)
    auto_duplicates = int(row.get("auto_duplicate_count", 0) or 0)

    if auto_applied > 0:
        return {
            "label": "GABUNG OTOMATIS",
            "class": "good",
            "meaning": f"{auto_applied} slot order lama sudah terisi dari chat susulan.",
        }
    if auto_duplicates > 0 or status == "DUPLIKAT":
        return {
            "label": "DUPLIKAT",
            "class": "neutral",
            "meaning": "Unit susulan sudah ada di order lama, tidak perlu tambah baris.",
        }
    if status == "SIAP_ISI_SLOT":
        return {
            "label": "SIAP GABUNG",
            "class": "good",
            "meaning": "Chat susulan cocok dengan order lama dan aman untuk mengisi slot kosong.",
        }
    if status == STAGE2_STATUS_CONFLICT:
        return {
            "label": "CONFLICT",
            "class": "bad",
            "meaning": "Chat membawa unit lama, tetapi ada atribut penting yang berubah sehingga output ditahan.",
        }
    if status == "TIDAK_COCOK":
        return {
            "label": "ORDER BARU",
            "class": "bad",
            "meaning": "Matcher tidak menemukan order lama yang cukup cocok.",
        }
    if action == "CHAT_TIDAK_MEMBAWA_UNIT_LENGKAP":
        return {
            "label": "DATA KURANG",
            "class": "warn",
            "meaning": "Chat masuk belum membawa unit lengkap untuk dicocokkan.",
        }
    return {
        "label": "CEK MANUAL",
        "class": "warn",
        "meaning": "Ada indikasi cocok, tetapi belum cukup aman untuk gabung otomatis.",
    }


def stage2_match_summary_metrics(rows: Sequence[Dict[str, object]]) -> Dict[str, int | float]:
    total = len(rows)
    ready = 0
    review = 0
    new_order = 0
    duplicate = 0
    auto_merge = 0
    avg_match = 0.0
    for row in rows:
        status = str(row.get("decision_status", "") or "")
        avg_match += float(row.get("p_match", 0.0) or 0.0)
        if int(row.get("auto_applied_count", 0) or 0) > 0:
            auto_merge += 1
        if status == "SIAP_ISI_SLOT":
            ready += 1
        elif status in {"PERLU_REVIEW", STAGE2_STATUS_CONFLICT}:
            review += 1
        elif status == "TIDAK_COCOK":
            new_order += 1
        elif status == "DUPLIKAT":
            duplicate += 1
    return {
        "total": total,
        "avg_match": avg_match / total if total else 0.0,
        "ready": ready,
        "review": review,
        "new_order": new_order,
        "duplicate": duplicate,
        "auto_merge": auto_merge,
    }


def stage2_confidence_label(row: Dict[str, object]) -> str:
    predicted = str(row.get("predicted_label", "") or "").strip().upper()
    status = str(row.get("decision_status", "") or "").strip().upper()
    confidence = float(row.get("confidence", 0.0) or 0.0)
    if status == STAGE2_STATUS_CONFLICT:
        return f"Conflict {pct_text(confidence)}"
    if predicted == LABEL_NO_MATCH or status == "TIDAK_COCOK":
        return f"Yakin NO_MATCH {pct_text(confidence)}"
    if predicted == LABEL_MATCH:
        return f"Yakin MATCH {pct_text(confidence)}"
    return f"Confidence keputusan {pct_text(confidence)}"


def stage2_candidate_rows_html(rows: Sequence[Dict[str, object]], limit: int = 8) -> str:
    if not rows:
        return "<div class='stage2-empty'>Tidak ada kandidat pencocokan.</div>"

    cards = []
    for idx, row in enumerate(rows[:limit], start=1):
        decision = stage2_operational_decision(row)
        p_match = float(row.get("p_match", 0.0) or 0.0)
        p_no_match = float(row.get("p_no_match", max(0.0, 1.0 - p_match)) or 0.0)
        confidence_text = stage2_confidence_label(row)
        cards.append(
            f"""
            <div class="stage2-candidate-card {decision['class']}">
                <div class="stage2-candidate-head">
                    <div class="stage2-candidate-title">Kandidat {idx}</div>
                </div>
                <div class="stage2-candidate-grid">
                    <div class="stage2-candidate-field">
                        <span>P_MATCH</span>
                        <strong>{pct_text(p_match)}</strong>
                    </div>
                    <div class="stage2-candidate-field">
                        <span>P_NO_MATCH</span>
                        <strong>{pct_text(p_no_match)}</strong>
                    </div>
                    <div class="stage2-candidate-field">
                        <span>Confidence keputusan</span>
                        <strong>{escape(confidence_text)}</strong>
                    </div>
                </div>
            </div>
            """
        )

    return (
        "<div class='stage2-candidate-list'>"
        f"{''.join(cards)}"
        "</div>"
    )


def stage2_snapshot_count(rows: Sequence[Dict[str, str]]) -> tuple[int, int, int]:
    total = len(rows)
    filled = sum(1 for row in rows if stage2_snapshot_identity_complete(row))
    return total, filled, max(0, total - filled)


def stage2_snapshot_status_class(row: Dict[str, str]) -> str:
    marker = str(row.get("_marker", "") or row.get("Status", "") or "").strip().upper()
    if marker == "BARU":
        return "new"
    if not stage2_snapshot_identity_complete(row):
        return "empty"
    return "filled"


def stage2_snapshot_table_html(rows: Sequence[Dict[str, str]]) -> str:
    if not rows:
        return "<div class='stage2-empty'>Snapshot belum tersedia.</div>"

    display_cols = [
        "Tgl RO",
        "Tgl Muat",
        "Pickup",
        "Tujuan",
        "No. Plat",
        "Type Truck",
        "Driver",
        "Kontak Driver",
        "Status",
    ]
    body = []
    for idx, row in enumerate(rows, start=1):
        status_class = stage2_snapshot_status_class(row)
        status = str(row.get("Status", "") or "").strip()
        if not status:
            status = "TERISI" if status_class == "filled" else "SLOT KOSONG"
        cells = [
            f"<td>{idx}</td>",
            *[
                (
                    f"<td><span class='stage2-unit-status {status_class}'>"
                    f"{escape(status)}</span></td>"
                    if col == "Status"
                    else f"<td>{escape(str(row.get(col, '') or ''))}</td>"
                )
                for col in display_cols
            ],
        ]
        body.append(f"<tr class='stage2-unit-row {status_class}'>{''.join(cells)}</tr>")

    headers = "".join(["<th>No.</th>"] + [f"<th>{escape(col)}</th>" for col in display_cols])
    return (
        "<div class='stage2-change-table-wrap'>"
        "<table class='stage2-change-table'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table>"
        "</div>"
    )


def stage2_order_change_html(row: Dict[str, object]) -> str:
    before_rows = row.get("before_rows", [])
    after_rows = row.get("after_rows", [])
    if not isinstance(before_rows, list):
        before_rows = []
    if not isinstance(after_rows, list):
        after_rows = []
    if not before_rows and not after_rows:
        return ""
    if before_rows and not after_rows:
        after_rows = [dict(item) for item in before_rows if isinstance(item, dict)]
    change_applied = stage2_apply_is_ready(row) or int(row.get("auto_applied_count", 0) or 0) > 0
    if not change_applied and stage2_blocks_smart_merge(row):
        return ""
    if not change_applied and before_rows:
        after_rows = [dict(item) for item in before_rows if isinstance(item, dict)]

    before_total, before_filled, before_empty = stage2_snapshot_count(before_rows)
    after_total, after_filled, after_empty = stage2_snapshot_count(after_rows)
    delta_filled = max(0, after_filled - before_filled)
    return f"""
    <div class="stage2-change">
        <div class="stage2-change-head">
            <div class="stage2-change-main-title">Output order</div>
            <div class="stage2-change-inline">
                <span>Terisi <strong>{before_filled}/{before_total} -> {after_filled}/{after_total}</strong></span>
                <span>Kosong <strong>{before_empty} -> {after_empty}</strong></span>
                <span>Masuk <strong>+{delta_filled}</strong></span>
            </div>
        </div>
        <div class="stage2-change-grid">
            <div class="stage2-change-box">
                <div class="stage2-change-title">Sebelum susulan</div>
                {stage2_snapshot_table_html(before_rows)}
            </div>
            <div class="stage2-change-box">
                <div class="stage2-change-title">Setelah susulan</div>
                {stage2_snapshot_table_html(after_rows)}
            </div>
        </div>
    </div>
    """


def render_stage2_match_card(
    rows: Sequence[Dict[str, object]],
    title: str,
    subtitle: str,
    height: int = 680,
) -> None:
    if not rows:
        st.info("Belum ada kandidat order belum lengkap dari DB untuk diuji oleh matcher tahap 2.")
        return

    top = rows[0]
    decision = stage2_operational_decision(top)
    metrics = stage2_match_summary_metrics(rows)
    top_match = float(top.get("p_match", 0.0) or 0.0)
    top_no_match = float(top.get("p_no_match", max(0.0, 1.0 - top_match)) or 0.0)
    top_conf = float(top.get("confidence", 0.0) or 0.0)
    top_conf_label = stage2_confidence_label(top)
    auto_applied = int(top.get("auto_applied_count", 0) or 0)
    auto_duplicates = int(top.get("auto_duplicate_count", 0) or 0)
    action_note = decision["meaning"]
    candidate_chat_text = resolve_stage2_candidate_chat_text(top)
    order_change_html = stage2_order_change_html(top)
    if auto_applied > 0:
        action_note = f"Auto-merge sudah diterapkan ke DB: {auto_applied} slot lama terisi."
    elif auto_duplicates > 0:
        action_note = f"{auto_duplicates} unit susulan terdeteksi duplikat dan tidak disimpan ulang."

    html = f"""
    <style>
    .stage2-audit {{
        height: {height}px;
        overflow: auto;
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #eef2f7;
        padding: 14px;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .stage2-card {{
        border: 1px solid #cbd5e1;
        border-left: 6px solid #16a34a;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        overflow: hidden;
    }}
    .stage2-card.warn {{ border-left-color: #d97706; }}
    .stage2-card.bad {{ border-left-color: #dc2626; }}
    .stage2-card.neutral {{ border-left-color: #64748b; }}
    .stage2-head {{
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: center;
        padding: 13px 16px;
        background: #f8fafc;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-card.good .stage2-head {{ background: #f0fdf4; }}
    .stage2-card.warn .stage2-head {{ background: #fffbeb; }}
    .stage2-card.bad .stage2-head {{ background: #fef2f2; }}
    .stage2-title {{
        font-size: 19px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .stage2-tag {{
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #fff;
        padding: 2px 9px;
        font-size: 10px;
        font-weight: 800;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0;
    }}
    .stage2-subtitle {{
        margin-top: 5px;
        font-size: 12px;
        color: #475569;
    }}
    .stage2-pills {{
        display: flex;
        justify-content: flex-end;
        gap: 6px;
        flex-wrap: wrap;
    }}
    .stage2-pills span {{
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #fff;
        padding: 6px 9px;
        font-size: 11px;
        font-weight: 700;
        color: #111827;
    }}
    .stage2-pills .stage2-status {{
        border-color: #22c55e;
        background: #dcfce7;
        color: #166534;
    }}
    .stage2-pills .stage2-status.warn {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    .stage2-pills .stage2-status.bad {{
        border-color: #ef4444;
        background: #fef2f2;
        color: #991b1b;
    }}
    .stage2-pills .stage2-status.neutral {{
        border-color: #94a3b8;
        background: #f8fafc;
        color: #334155;
    }}
    .stage2-body {{ padding: 14px 16px 16px; }}
    .stage2-metrics {{
        display: grid;
        grid-template-columns: repeat(5, minmax(120px, 1fr));
        gap: 10px;
        margin-bottom: 14px;
    }}
    .stage2-metric {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #fff;
        padding: 10px 12px;
    }}
    .stage2-metric-label {{
        font-size: 11px;
        color: #475569;
        margin-bottom: 5px;
    }}
    .stage2-metric-value {{
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-score-strip {{
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 10px;
        margin-bottom: 12px;
    }}
    .stage2-score {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #ffffff;
        padding: 9px 11px;
    }}
    .stage2-score-label {{
        font-size: 11px;
        color: #475569;
        margin-bottom: 4px;
    }}
    .stage2-score-value {{
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-score-value.small {{
        font-size: 15px;
        line-height: 1.25;
    }}
    .stage2-grid {{
        display: grid;
        grid-template-columns: minmax(300px, 0.9fr) minmax(420px, 1.1fr);
        gap: 12px;
        margin-bottom: 12px;
    }}
    .stage2-panel {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #fff;
        overflow: hidden;
    }}
    .stage2-panel-title {{
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
        padding: 10px 12px;
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-pre {{
        margin: 0;
        padding: 13px 14px;
        min-height: 180px;
        max-height: 280px;
        overflow: auto;
        background: #fbfdfc;
        color: #020617;
        font-size: 12px;
        line-height: 1.55;
        white-space: pre-wrap;
        font-family: Consolas, "Courier New", monospace;
    }}
    .stage2-note {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #f8fafc;
        padding: 10px 12px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #334155;
        line-height: 1.45;
    }}
    .stage2-note strong {{ color: #0f172a; }}
    .stage2-change {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
        margin-bottom: 12px;
    }}
    .stage2-change-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
        padding: 9px 12px;
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-change-main-title {{
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-change-inline {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .stage2-change-inline span {{
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #ffffff;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 800;
        color: #334155;
        white-space: nowrap;
    }}
    .stage2-change-inline strong {{
        color: #0f172a;
    }}
    .stage2-change-summary {{
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 8px;
        padding: 10px 12px;
        background: #f8fafc;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-change-summary div {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #ffffff;
        padding: 8px 10px;
    }}
    .stage2-change-summary span {{
        display: block;
        font-size: 10px;
        color: #475569;
        margin-bottom: 3px;
    }}
    .stage2-change-summary strong {{
        font-size: 15px;
        color: #0f172a;
    }}
    .stage2-change-impact {{
        margin: 10px 12px 0;
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #f8fafc;
        padding: 8px 10px;
        font-size: 12px;
        color: #334155;
        font-weight: 700;
    }}
    .stage2-change-impact.good {{
        border-color: #86efac;
        background: #f0fdf4;
        color: #166534;
    }}
    .stage2-change-impact.neutral {{
        border-color: #cbd5e1;
        background: #f8fafc;
        color: #334155;
    }}
    .stage2-change-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        padding: 12px;
    }}
    .stage2-change-box {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        overflow: hidden;
        background: #ffffff;
    }}
    .stage2-change-title {{
        padding: 8px 10px;
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
        font-size: 12px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-change-table-wrap {{
        max-height: 260px;
        overflow-y: auto;
        overflow-x: hidden;
    }}
    .stage2-change-table {{
        width: 100%;
        min-width: 0;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 9px;
    }}
    .stage2-change-table th {{
        background: #e58d90;
        color: #000;
        border: 1px solid #111827;
        padding: 5px 4px;
        text-align: center;
        font-weight: 800;
        word-break: break-word;
    }}
    .stage2-change-table td {{
        background: #ffffff;
        border: 1px solid #111827;
        padding: 5px 4px;
        text-align: center;
        color: #000;
        word-break: break-word;
    }}
    .stage2-change-table tr.empty td {{ background: #fff4b8; }}
    .stage2-change-table tr.new td {{ background: #ecfdf3; }}
    .stage2-unit-status {{
        display: inline-block;
        border: 1px solid #94a3b8;
        border-radius: 999px;
        padding: 2px 6px;
        font-size: 9px;
        font-weight: 800;
        background: #f8fafc;
        color: #334155;
        white-space: nowrap;
    }}
    .stage2-unit-status.new {{
        border-color: #22c55e;
        background: #dcfce7;
        color: #166534;
    }}
    .stage2-unit-status.empty {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    .stage2-candidate-list {{
        display: grid;
        gap: 10px;
        padding: 12px;
        background: #ffffff;
    }}
    .stage2-candidate-card {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
    }}
    .stage2-candidate-card.good {{ border-left: 4px solid #16a34a; }}
    .stage2-candidate-card.warn {{ border-left: 4px solid #d97706; }}
    .stage2-candidate-card.bad {{ border-left: 4px solid #dc2626; }}
    .stage2-candidate-card.neutral {{ border-left: 4px solid #64748b; }}
    .stage2-candidate-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 11px;
        border-bottom: 1px solid #d6dee8;
        background: #f8fafc;
    }}
    .stage2-candidate-title {{
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-candidate-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 8px;
        padding: 10px 11px 11px;
    }}
    .stage2-candidate-field,
    .stage2-candidate-reason {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #fbfdff;
        padding: 8px 9px;
        min-width: 0;
    }}
    .stage2-candidate-card.good .stage2-candidate-field {{
        border-color: #86efac;
        background: #f0fdf4;
    }}
    .stage2-candidate-card.warn .stage2-candidate-field {{
        border-color: #facc15;
        background: #fffbeb;
    }}
    .stage2-candidate-card.bad .stage2-candidate-field {{
        border-color: #fca5a5;
        background: #fef2f2;
    }}
    .stage2-candidate-card.neutral .stage2-candidate-field {{
        border-color: #cbd5e1;
        background: #f8fafc;
    }}
    .stage2-candidate-field span,
    .stage2-candidate-reason span {{
        display: block;
        color: #64748b;
        font-size: 10px;
        margin-bottom: 3px;
    }}
    .stage2-candidate-field strong,
    .stage2-candidate-reason strong {{
        display: block;
        color: #0f172a;
        font-size: 12px;
        line-height: 1.35;
        word-break: break-word;
    }}
    .stage2-candidate-reason {{
        margin: 8px 11px 11px;
    }}
    .stage2-status {{
        display: inline-block;
        border: 1px solid #22c55e;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 800;
        white-space: nowrap;
    }}
    .stage2-status.warn {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    .stage2-status.bad {{
        border-color: #ef4444;
        background: #fef2f2;
        color: #991b1b;
    }}
    .stage2-status.neutral {{
        border-color: #94a3b8;
        background: #f8fafc;
        color: #334155;
    }}
    .stage2-empty {{
        padding: 14px;
        color: #475569;
        font-size: 12px;
    }}
    @media (max-width: 980px) {{
        .stage2-head {{ align-items: flex-start; flex-direction: column; }}
        .stage2-pills {{ justify-content: flex-start; }}
        .stage2-metrics {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
        .stage2-score-strip {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
        .stage2-candidate-grid {{ grid-template-columns: 1fr; }}
        .stage2-grid {{ grid-template-columns: 1fr; }}
        .stage2-change-grid {{ grid-template-columns: 1fr; }}
        .stage2-change-summary {{ grid-template-columns: 1fr; }}
    }}
    </style>
    <div class="stage2-audit">
        <section class="stage2-card {decision['class']}">
            <div class="stage2-head">
                <div>
                    <div class="stage2-title">
                        <span>{escape(title)}</span>
                        <span class="stage2-tag">Sequence Pair Matching</span>
                    </div>
                    <div class="stage2-subtitle">{escape(subtitle)}</div>
                </div>
                <div class="stage2-pills">
                    <span>Order kandidat {escape(str(metrics['total']))}</span>
                    <span>{escape(top_conf_label)}</span>
                </div>
            </div>
            <div class="stage2-body">
                <div class="stage2-score-strip">
                    <div class="stage2-score">
                        <div class="stage2-score-label">P_MATCH</div>
                        <div class="stage2-score-value">{pct_text(top_match)}</div>
                    </div>
                    <div class="stage2-score">
                        <div class="stage2-score-label">P_NO_MATCH</div>
                        <div class="stage2-score-value">{pct_text(top_no_match)}</div>
                    </div>
                    <div class="stage2-score">
                        <div class="stage2-score-label">Confidence keputusan</div>
                        <div class="stage2-score-value small">{escape(top_conf_label)}</div>
                    </div>
                </div>
                <div class="stage2-note">
                    <strong>Penilaian:</strong> {escape(action_note)}
                </div>
                <div class="stage2-grid">
                    <div class="stage2-panel">
                        <div class="stage2-panel-title">Pesanan awal / chat asli</div>
                        <pre class="stage2-pre">{escape(candidate_chat_text or 'Raw chat pesanan awal belum tersedia di DB audit lama.')}</pre>
                    </div>
                    <div class="stage2-panel">
                        <div class="stage2-panel-title">Pesanan susulan / chat masuk</div>
                        <pre class="stage2-pre">{escape(str(top.get('incoming_text', '') or '-'))}</pre>
                    </div>
                </div>
                {order_change_html}
            </div>
        </section>
    </div>
    """
    st.html(html)


def render_stage2_match_preview(preview_rows: Sequence[Dict[str, object]], key_prefix: str) -> None:
    render_stage2_match_card(
        preview_rows,
        title="Analitik pencocokan order",
        subtitle=(
            "Membandingkan chat masuk dengan order belum lengkap di DB untuk menentukan "
            "gabung otomatis, duplikat, order baru, atau cek manual."
        ),
    )


def load_stage2_match_history(limit: int = 50) -> List[Dict[str, object]]:
    if not DB_PERSISTENCE_ENABLED or db_load_stage2_match_audits is None:
        return []
    return list(db_load_stage2_match_audits(limit) or [])


def latest_stage2_match_group(limit: int = 50) -> List[Dict[str, object]]:
    history = load_stage2_match_history(limit)
    if not history:
        return []

    latest = history[0]
    latest_raw_chat_id = str(latest.get("raw_chat_id", "") or "").strip()
    if latest_raw_chat_id:
        rows = [
            row
            for row in history
            if str(row.get("raw_chat_id", "") or "").strip() == latest_raw_chat_id
        ]
    else:
        latest_time = str(latest.get("created_at", "") or "")[:19]
        rows = [
            row
            for row in history
            if str(row.get("created_at", "") or "")[:19] == latest_time
        ]

    return sorted(
        rows,
        key=lambda row: float(row.get("p_match", 0.0) or 0.0),
        reverse=True,
    )


def stage2_audit_event_key(row: Dict[str, object]) -> str:
    raw_chat_id = str(row.get("raw_chat_id", "") or "").strip()
    if raw_chat_id:
        return raw_chat_id
    created_at = str(row.get("created_at", "") or "")[:19]
    incoming_text = str(row.get("incoming_text", "") or "").strip()
    return f"{created_at}|{incoming_text[:120]}"


def stage2_top_events_from_history(history: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in history:
        if not isinstance(row, dict):
            continue
        key = stage2_audit_event_key(row)
        if not key:
            continue
        grouped.setdefault(key, []).append(row)

    events: List[Dict[str, object]] = []
    for rows in grouped.values():
        ranked = sorted(
            rows,
            key=lambda item: float(item.get("p_match", 0.0) or 0.0),
            reverse=True,
        )
        if not ranked:
            continue
        top = dict(ranked[0])
        top["_candidate_count"] = len(ranked)
        events.append(top)

    return sorted(
        events,
        key=lambda item: str(item.get("created_at", "") or ""),
    )


def stage2_order_timeline_groups_from_events(
    events: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    groups: Dict[str, Dict[str, object]] = {}
    for event in events:
        candidate_key = str(event.get("candidate_key", "") or "").strip()
        candidate_summary = str(event.get("candidate_summary", "") or "").strip()
        group_key = candidate_key or candidate_summary or stage2_audit_event_key(event)
        if group_key not in groups:
            groups[group_key] = {
                "key": group_key,
                "summary": candidate_summary or group_key,
                "events": [],
            }
        groups[group_key]["events"].append(event)
        if candidate_summary:
            groups[group_key]["summary"] = candidate_summary

    ordered = list(groups.values())
    ordered.sort(
        key=lambda group: str((group.get("events") or [{}])[-1].get("created_at", "") or ""),
        reverse=True,
    )
    return ordered


def stage2_order_timeline_groups(history: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    events = stage2_top_events_from_history(history)
    return stage2_order_timeline_groups_from_events(events)


def stage2_event_has_merge(event: Dict[str, object]) -> bool:
    return stage2_apply_is_ready(event) or int(event.get("auto_applied_count", 0) or 0) > 0


def stage2_is_confident_match_merge(event: Dict[str, object]) -> bool:
    p_match = float(event.get("p_match", 0.0) or 0.0)
    return (
        stage2_event_predicted_label(event) == LABEL_MATCH
        and p_match >= STAGE2_STRONG_MATCH_THRESHOLD
        and stage2_event_has_merge(event)
    )


def stage2_anomaly_label(event: Dict[str, object]) -> str:
    if stage2_is_confident_match_merge(event):
        return ""
    if bool(event.get("date_conflict", False)):
        return ""

    p_match = float(event.get("p_match", 0.0) or 0.0)
    predicted = stage2_event_predicted_label(event)
    has_merge = stage2_event_has_merge(event)
    decision_status = str(event.get("decision_status", "") or "").upper()
    incoming_complete = int(event.get("incoming_complete_units", 0) or 0)
    overflow_units = int(event.get("overflow_units", 0) or 0)
    duplicate_units = int(event.get("duplicate_units", 0) or 0)
    proposed_fill = int(event.get("proposed_fill_count", 0) or 0)

    if decision_status == STAGE2_STATUS_CONFLICT:
        reason = str(event.get("policy_reason", "") or "").strip()
        return reason or "Conflict atribut unit lama"
    if predicted == LABEL_NO_MATCH and p_match < STAGE2_CLEAR_NEW_ORDER_MAX_MATCH:
        return ""
    if overflow_units > 0:
        return "Konflik slot"
    if incoming_complete <= 0:
        return "Data unit belum lengkap"
    if predicted == LABEL_MATCH and not has_merge:
        if duplicate_units > 0 and proposed_fill <= 0:
            return "Duplikat unit lama"
        return "MATCH tidak aman"
    if decision_status == "PERLU_REVIEW":
        return "Perlu audit"
    if STAGE2_CLEAR_NEW_ORDER_MAX_MATCH <= p_match < STAGE2_STRONG_MATCH_THRESHOLD:
        return "Model ragu"
    return ""


def stage2_is_anomaly_event(event: Dict[str, object]) -> bool:
    return bool(stage2_anomaly_label(event))


def stage2_event_predicted_label(event: Dict[str, object]) -> str:
    predicted = str(event.get("predicted_label", "") or "").strip().upper()
    if predicted in {LABEL_MATCH, LABEL_NO_MATCH}:
        return predicted
    p_match = float(event.get("p_match", 0.0) or 0.0)
    p_no_match = float(event.get("p_no_match", max(0.0, 1.0 - p_match)) or 0.0)
    return LABEL_MATCH if p_match >= p_no_match else LABEL_NO_MATCH


def stage2_is_clear_new_order(event: Dict[str, object]) -> bool:
    decision = stage2_operational_decision(event)
    if str(decision.get("label", "") or "").strip().upper() != "ORDER BARU":
        return False
    p_match = float(event.get("p_match", 0.0) or 0.0)
    predicted = stage2_event_predicted_label(event)
    return predicted == LABEL_NO_MATCH and p_match < STAGE2_CLEAR_NEW_ORDER_MAX_MATCH


def filter_stage2_top_events(
    events: Sequence[Dict[str, object]],
    model_filter: str,
    decision_filter: str,
) -> List[Dict[str, object]]:
    filtered: List[Dict[str, object]] = []
    for event in events:
        predicted = stage2_event_predicted_label(event)
        is_clear_new_order = stage2_is_clear_new_order(event)
        decision = stage2_operational_decision(event)
        label = str(decision.get("label", "") or "").strip().upper()

        if model_filter == "Positif (MATCH)" and predicted != LABEL_MATCH:
            continue
        if model_filter == "Negatif perlu audit" and (
            predicted != LABEL_NO_MATCH or is_clear_new_order
        ):
            continue
        if model_filter == "Order baru jelas" and not is_clear_new_order:
            continue

        if decision_filter == "Gabung" and label not in {"SIAP GABUNG", "GABUNG OTOMATIS"}:
            continue
        if decision_filter == "Order baru" and label != "ORDER BARU":
            continue
        if decision_filter == "Cek manual" and label not in {"CEK MANUAL", "DATA KURANG"}:
            continue
        if decision_filter == "Duplikat" and label != "DUPLIKAT":
            continue

        filtered.append(event)
    return filtered


def filter_stage2_timeline_groups(
    groups: Sequence[Dict[str, object]],
    timeline_filter: str,
) -> List[Dict[str, object]]:
    filtered: List[Dict[str, object]] = []
    for group in groups:
        events = list(group.get("events", []) or [])
        has_merge = any(stage2_event_has_merge(event) for event in events)
        if timeline_filter == "Bertahap" and len(events) <= 1:
            continue
        if timeline_filter == "Satu tahap" and len(events) != 1:
            continue
        if timeline_filter == "Ada gabung" and not has_merge:
            continue
        if timeline_filter == "Tanpa gabung" and has_merge:
            continue
        filtered.append(group)
    return filtered


def stage2_rows_to_dataframe(rows: Sequence[Dict[str, object]] | None) -> pd.DataFrame:
    safe_rows = [dict(row) for row in (rows or []) if isinstance(row, dict)]
    if not safe_rows:
        return pd.DataFrame(columns=EXCEL_COLUMNS)
    return pd.DataFrame(safe_rows)


def stage2_first_filled_from_rows(rows: Sequence[Dict[str, object]] | None, col: str) -> str:
    return stage2_first_filled(stage2_rows_to_dataframe(rows), col)


def stage2_event_incoming_rows(event: Dict[str, object]) -> List[Dict[str, object]]:
    incoming_rows = [
        dict(row)
        for row in (event.get("incoming_rows", []) or [])
        if isinstance(row, dict)
    ]
    if incoming_rows:
        return incoming_rows

    after_rows = [
        dict(row)
        for row in (event.get("after_rows", []) or [])
        if isinstance(row, dict)
    ]
    marked_rows = [
        row
        for row in after_rows
        if str(row.get("_marker", "") or "").strip().upper() == "BARU"
    ]
    return marked_rows


def stage2_event_candidate_source_rows(event: Dict[str, object]) -> List[Dict[str, object]]:
    source_rows = [
        dict(row)
        for row in (event.get("candidate_source_rows", []) or [])
        if isinstance(row, dict)
    ]
    if source_rows:
        return source_rows
    return [
        dict(row)
        for row in (event.get("before_rows", []) or [])
        if isinstance(row, dict)
    ]


def stage2_evidence_compare_card(
    label: str,
    candidate_value: str,
    incoming_value: str,
) -> str:
    left = str(candidate_value or "").strip()
    right = str(incoming_value or "").strip()
    if filled_value(left) and filled_value(right):
        is_match = stage2_norm_key(left) == stage2_norm_key(right)
        status_label = "COCOK" if is_match else "BEDA"
        status_class = "good" if is_match else "bad"
    else:
        status_label = "BELUM LENGKAP"
        status_class = "warn"

    return f"""
    <div class="stage2-evidence-card {status_class}">
        <div class="stage2-evidence-top">
            <span>{escape(label)}</span>
            <strong>{escape(status_label)}</strong>
        </div>
        <div class="stage2-evidence-values">
            <div>
                <span>Order awal</span>
                <strong>{escape(left or '-')}</strong>
            </div>
            <div>
                <span>Chat masuk</span>
                <strong>{escape(right or '-')}</strong>
            </div>
        </div>
    </div>
    """


def stage2_slot_evidence_card(event: Dict[str, object]) -> str:
    source_rows = stage2_event_candidate_source_rows(event)
    before_empty = sum(1 for row in source_rows if is_partial_visual_row(row))
    if before_empty <= 0:
        before_empty = int(event.get("empty", 0) or 0)

    incoming_rows = stage2_event_incoming_rows(event)
    incoming_df = stage2_rows_to_dataframe(incoming_rows)
    incoming_complete = int(event.get("incoming_complete_units", 0) or 0)
    if incoming_complete <= 0 and not incoming_df.empty:
        incoming_complete = len(stage2_complete_unit_rows(incoming_df))

    proposed_fill = int(event.get("proposed_fill_count", 0) or 0)
    if proposed_fill <= 0:
        proposed_fill = sum(
            1
            for row in (event.get("after_rows", []) or [])
            if isinstance(row, dict)
            and str(row.get("_marker", "") or "").strip().upper() == "BARU"
        )

    if before_empty > 0 and proposed_fill > 0 and proposed_fill <= before_empty:
        status_label = "CUKUP"
        status_class = "good"
    elif before_empty <= 0:
        status_label = "PENUH"
        status_class = "bad"
    elif proposed_fill > before_empty:
        status_label = "MELEBIHI"
        status_class = "warn"
    else:
        status_label = "BELUM ADA UNIT"
        status_class = "warn"

    return f"""
    <div class="stage2-evidence-card {status_class}">
        <div class="stage2-evidence-top">
            <span>Slot kosong</span>
            <strong>{escape(status_label)}</strong>
        </div>
        <div class="stage2-evidence-values stage2-evidence-slot">
            <div>
                <span>Order awal</span>
                <strong>{before_empty} slot kosong</strong>
            </div>
            <div>
                <span>Chat masuk</span>
                <strong>{incoming_complete} unit lengkap, masuk {proposed_fill}</strong>
            </div>
        </div>
    </div>
    """


def stage2_unit_identity_label(row: Dict[str, object]) -> str:
    driver = str(row.get("Driver", row.get("driver", "")) or "").strip()
    plate = str(row.get("No. Plat", row.get("no_plat", "")) or "").strip()
    phone = str(row.get("Kontak Driver", row.get("kontak_driver", "")) or "").strip()
    return " | ".join(part for part in (driver, plate, phone) if filled_value(part))


def stage2_identity_evidence_card(event: Dict[str, object]) -> str:
    before_rows = [
        row
        for row in stage2_event_candidate_source_rows(event)
        if stage2_has_complete_identity(row)
    ]
    incoming_rows = [
        row
        for row in stage2_event_incoming_rows(event)
        if stage2_has_complete_identity(row)
    ]

    matched_rows = []
    for before_row in before_rows:
        before_signature = stage2_identity_signature(before_row)
        if any(
            stage2_identity_is_duplicate(before_signature, stage2_identity_signature(incoming_row))
            for incoming_row in incoming_rows
        ):
            matched_rows.append(before_row)

    total_registered = len(before_rows)
    matched_count = len(matched_rows)
    if total_registered <= 0:
        status_label = "BELUM ADA"
        status_class = "warn"
    elif matched_count > 0:
        status_label = f"{matched_count}/{total_registered} COCOK"
        status_class = "good"
    else:
        status_label = "0 COCOK"
        status_class = "warn"

    if matched_rows:
        first_match = stage2_unit_identity_label(matched_rows[0])
        extra = matched_count - 1
        detail_value = first_match if extra <= 0 else f"{first_match} +{extra} unit"
    elif total_registered:
        detail_value = f"{total_registered} unit lama terdaftar"
    else:
        detail_value = "-"

    incoming_value = (
        f"{matched_count} dari {len(incoming_rows)} unit masuk terdeteksi sebagai unit lama"
        if matched_count
        else f"{len(incoming_rows)} unit lengkap masuk"
    )

    return f"""
    <div class="stage2-evidence-card stage2-evidence-card-wide {status_class}">
        <div class="stage2-evidence-top">
            <span>Unit lama terdeteksi</span>
            <strong>{escape(status_label)}</strong>
        </div>
        <div class="stage2-evidence-single">
            <span>{escape(incoming_value)}</span>
            <strong title="{escape(detail_value)}">{escape(detail_value)}</strong>
        </div>
    </div>
    """


def stage2_qty_evidence_card(event: Dict[str, object]) -> str:
    before_rows = stage2_event_candidate_source_rows(event)
    incoming_rows = stage2_event_incoming_rows(event)
    before_total = int(event.get("qty_target", 0) or 0)
    if before_total <= 0:
        before_total = len(before_rows)
    incoming_total = len(incoming_rows)

    if before_total > 0 and incoming_total > 0:
        is_match = before_total == incoming_total
        status_label = "COCOK" if is_match else "BEDA"
        status_class = "good" if is_match else "bad"
    else:
        status_label = "BELUM LENGKAP"
        status_class = "warn"

    return f"""
    <div class="stage2-evidence-card {status_class}">
        <div class="stage2-evidence-top">
            <span>Qty Unit</span>
            <strong>{escape(status_label)}</strong>
        </div>
        <div class="stage2-evidence-values">
            <div>
                <span>Order awal</span>
                <strong>{before_total or '-'}</strong>
            </div>
            <div>
                <span>Chat masuk</span>
                <strong>{incoming_total or '-'}</strong>
            </div>
        </div>
    </div>
    """


def stage2_unit_change_evidence_card(event: Dict[str, object]) -> str:
    before_rows = stage2_event_candidate_source_rows(event)
    incoming_rows = stage2_event_incoming_rows(event)
    matched_units = stage2_match_registered_units(before_rows, incoming_rows)
    watched_fields = [
        ("Tgl Muat", "waktu loading"),
        ("Driver", "driver"),
        ("No. Plat", "nopol"),
        ("Kontak Driver", "no hp"),
    ]

    changes: List[str] = []
    for match in matched_units:
        existing = match.get("existing", {})
        incoming = match.get("incoming", {})
        unit_label = stage2_unit_identity_label(existing) or "unit lama"
        for field, label in watched_fields:
            left = stage2_row_value(existing, field)
            right = stage2_row_value(incoming, field)
            if stage2_values_differ(left, right):
                changes.append(f"{label}: {unit_label} ({left or '-'} -> {right or '-'})")

    if changes:
        status_label = "BERUBAH"
        status_class = "bad"
        detail_value = " ; ".join(changes[:3])
        if len(changes) > 3:
            detail_value += f" +{len(changes) - 3} perubahan"
        subtitle = f"{len(changes)} perubahan pada unit lama terdeteksi"
    elif matched_units:
        status_label = "STABIL"
        status_class = "good"
        detail_value = f"{len(matched_units)} unit lama tidak berubah"
        subtitle = "Driver, nopol, no HP, dan waktu loading unit lama konsisten"
    else:
        status_label = "BELUM ADA"
        status_class = "warn"
        detail_value = "-"
        subtitle = "Belum ada unit lama yang bisa dibandingkan"

    return f"""
    <div class="stage2-evidence-card stage2-evidence-card-wide {status_class}">
        <div class="stage2-evidence-top">
            <span>Perubahan unit lama</span>
            <strong>{escape(status_label)}</strong>
        </div>
        <div class="stage2-evidence-single">
            <span>{escape(subtitle)}</span>
            <strong title="{escape(detail_value)}">{escape(detail_value)}</strong>
        </div>
    </div>
    """


def stage2_match_evidence_html(event: Dict[str, object]) -> str:
    before_rows = stage2_event_candidate_source_rows(event)
    incoming_rows = stage2_event_incoming_rows(event)
    cards = [
        stage2_qty_evidence_card(event),
        stage2_evidence_compare_card(
            "Tgl RO",
            stage2_first_filled_from_rows(before_rows, "Tgl RO"),
            stage2_first_filled_from_rows(incoming_rows, "Tgl RO"),
        ),
        stage2_evidence_compare_card(
            "Pickup",
            stage2_first_filled_from_rows(before_rows, "Pickup"),
            stage2_first_filled_from_rows(incoming_rows, "Pickup"),
        ),
        stage2_evidence_compare_card(
            "Rute/Tujuan",
            stage2_first_filled_from_rows(before_rows, "Tujuan"),
            stage2_first_filled_from_rows(incoming_rows, "Tujuan"),
        ),
        stage2_evidence_compare_card(
            "Tipe Unit",
            stage2_first_filled_from_rows(before_rows, "Type Truck"),
            stage2_first_filled_from_rows(incoming_rows, "Type Truck"),
        ),
        stage2_identity_evidence_card(event),
        stage2_unit_change_evidence_card(event),
        stage2_slot_evidence_card(event),
    ]
    return f"""
    <div class="stage2-evidence">
        <div class="stage2-evidence-title">Bukti konteks pencocokan</div>
        <div class="stage2-evidence-grid">{''.join(cards)}</div>
    </div>
    """


def render_stage2_match_order_timeline(
    history: Sequence[Dict[str, object]] | None = None,
    groups: Sequence[Dict[str, object]] | None = None,
    title: str = "Evaluasi pencocokan order",
    subtitle: str = "Riwayat rekonsiliasi dikelompokkan per order kandidat.",
    height: int = 780,
    max_orders: int = 12,
) -> None:
    if groups is None:
        groups = stage2_order_timeline_groups(history or [])
    if not groups:
        st.info("Belum ada audit pencocokan yang bisa dikelompokkan per order.")
        return

    order_cards = []
    for group_index, group in enumerate(groups[:max_orders], start=1):
        events = list(group.get("events", []) or [])
        if not events:
            continue
        latest_event = events[-1]
        latest_decision = stage2_operational_decision(latest_event)
        latest_created = str(latest_event.get("created_at", "") or "")[:19]
        event_cards = []
        for event_index, event in enumerate(events, start=1):
            decision = stage2_operational_decision(event)
            p_match = float(event.get("p_match", 0.0) or 0.0)
            p_no_match = float(event.get("p_no_match", max(0.0, 1.0 - p_match)) or 0.0)
            confidence_text = stage2_confidence_label(event)
            anomaly_label = stage2_anomaly_label(event)
            candidate_chat_text = resolve_stage2_candidate_chat_text(event)
            evidence_html = stage2_match_evidence_html(event)
            change_html = stage2_order_change_html(event)
            details_open = ""
            event_cards.append(
                f"""
                <article class="stage2-timeline-event {decision['class']}">
                    <div class="stage2-event-head">
                        <div class="stage2-event-title">Tahap {event_index}</div>
                        <div class="stage2-event-pills">
                            <span>Match {pct_text(p_match)}</span>
                            <span>No match {pct_text(p_no_match)}</span>
                            <span>{escape(confidence_text)}</span>
                            {f"<span class='stage2-status warn'>{escape(anomaly_label)}</span>" if anomaly_label else ""}
                        </div>
                    </div>
                    {evidence_html}
                    <details class="stage2-event-detail"{details_open}>
                        <summary>Detail tahap {event_index}</summary>
                        <div class="stage2-timeline-chat-grid">
                            <div class="stage2-panel">
                                <div class="stage2-panel-title">Pesanan awal / chat asli</div>
                                <pre class="stage2-pre">{escape(candidate_chat_text or 'Raw chat pesanan awal belum tersedia di DB audit lama.')}</pre>
                            </div>
                            <div class="stage2-panel">
                                <div class="stage2-panel-title">Pesanan susulan / chat masuk</div>
                                <pre class="stage2-pre">{escape(str(event.get('incoming_text', '') or '-'))}</pre>
                            </div>
                        </div>
                        {change_html}
                    </details>
                </article>
                """
            )

        order_cards.append(
            f"""
            <section class="stage2-order-timeline-card">
                <div class="stage2-order-timeline-head">
                    <div class="stage2-order-main">
                        <div class="stage2-order-title-row">
                            <div class="stage2-order-title">Order pencocokan #{group_index}</div>
                            <span class="stage2-order-time">{escape(latest_created or '-')}</span>
                        </div>
                        <div class="stage2-order-summary">{escape(str(group.get('summary', '') or '-'))}</div>
                    </div>
                    <div class="stage2-order-kicker">prediksi indobenchmark\\indobert-base-p2</div>
                </div>
                <div class="stage2-order-events">
                    {''.join(event_cards)}
                </div>
            </section>
            """
        )

    html = f"""
    <style>
    .stage2-timeline-audit {{
        height: {height}px;
        overflow: auto;
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #eef2f7;
        padding: 14px;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .stage2-timeline-page-head {{
        display: none;
    }}
    .stage2-timeline-page-title {{
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-timeline-page-subtitle {{
        margin-top: 4px;
        font-size: 12px;
        color: #475569;
    }}
    .stage2-order-timeline-card {{
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    }}
    .stage2-order-timeline-head {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 13px 16px;
        border-bottom: 1px solid #d6dee8;
        background: #ffffff;
    }}
    .stage2-order-main {{
        min-width: 0;
    }}
    .stage2-order-title-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .stage2-order-time {{
        display: inline-flex;
        align-items: center;
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #f8fafc;
        padding: 6px 10px;
        color: #111827;
        font-size: 12px;
        font-weight: 800;
        white-space: nowrap;
    }}
    .stage2-order-kicker {{
        display: inline-flex;
        align-items: center;
        width: fit-content;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        background: #eff6ff;
        padding: 8px 13px;
        margin-left: auto;
        color: #1d4ed8;
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 0;
        white-space: nowrap;
        flex-shrink: 0;
    }}
    .stage2-order-title {{
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-order-summary {{
        margin-top: 5px;
        font-size: 12px;
        color: #475569;
        line-height: 1.4;
    }}
    .stage2-order-pills {{
        display: flex;
        justify-content: flex-end;
        gap: 6px;
        flex-wrap: wrap;
    }}
    .stage2-order-pills span {{
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #f8fafc;
        padding: 9px 13px;
        font-size: 13px;
        font-weight: 800;
        color: #111827;
        white-space: nowrap;
    }}
    .stage2-order-events {{
        padding: 12px;
        display: grid;
        gap: 12px;
    }}
    .stage2-timeline-event {{
        border: 1px solid #d6dee8;
        border-left: 5px solid #16a34a;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
    }}
    .stage2-timeline-event.warn {{ border-left-color: #d97706; }}
    .stage2-timeline-event.bad {{ border-left-color: #dc2626; }}
    .stage2-timeline-event.neutral {{ border-left-color: #64748b; }}
    .stage2-event-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 9px 12px;
        background: #ffffff;
        border-bottom: 1px solid #d6dee8;
        flex-wrap: wrap;
    }}
    .stage2-event-title {{
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-event-pills {{
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .stage2-event-pills span {{
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #f8fafc;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 800;
        color: #334155;
        white-space: nowrap;
    }}
    .stage2-evidence {{
        padding: 10px 12px 12px;
        border-bottom: 1px solid #d6dee8;
        background: #ffffff;
    }}
    .stage2-evidence-title {{
        margin-bottom: 8px;
        font-size: 12px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-evidence-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
    }}
    .stage2-evidence-card {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #fbfdff;
        overflow: hidden;
    }}
    .stage2-evidence-card.good {{
        border-color: #86efac;
        background: #f0fdf4;
    }}
    .stage2-evidence-card.warn {{
        border-color: #facc15;
        background: #fffbeb;
    }}
    .stage2-evidence-card.bad {{
        border-color: #fca5a5;
        background: #fef2f2;
    }}
    .stage2-evidence-card-wide {{
        grid-column: auto;
    }}
    .stage2-evidence-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        padding: 7px 9px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.45);
    }}
    .stage2-evidence-top span {{
        color: #475569;
        font-size: 11px;
        font-weight: 700;
    }}
    .stage2-evidence-top strong {{
        color: #0f172a;
        font-size: 11px;
        font-weight: 900;
        white-space: nowrap;
    }}
    .stage2-evidence-values {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0;
    }}
    .stage2-evidence-values div {{
        padding: 8px 9px;
        min-width: 0;
    }}
    .stage2-evidence-values div + div {{
        border-left: 1px solid rgba(148, 163, 184, 0.45);
    }}
    .stage2-evidence-values span {{
        display: block;
        color: #64748b;
        font-size: 10px;
        margin-bottom: 3px;
    }}
    .stage2-evidence-values strong {{
        display: block;
        color: #0f172a;
        font-size: 12px;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }}
    .stage2-evidence-single {{
        padding: 8px 9px;
        min-width: 0;
    }}
    .stage2-evidence-single span {{
        display: block;
        color: #64748b;
        font-size: 10px;
        margin-bottom: 3px;
    }}
    .stage2-evidence-single strong {{
        display: block;
        color: #0f172a;
        font-size: 12px;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }}
    .stage2-event-time {{
        margin-top: 2px;
        font-size: 11px;
        color: #64748b;
    }}
    .stage2-event-scores {{
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 9px;
        padding: 10px 12px;
    }}
    .stage2-event-scores div {{
        border: 1px solid #d6dee8;
        border-radius: 7px;
        background: #fbfdff;
        padding: 8px 10px;
    }}
    .stage2-timeline-event.good .stage2-event-scores div {{
        border-color: #86efac;
        background: #f0fdf4;
    }}
    .stage2-timeline-event.warn .stage2-event-scores div {{
        border-color: #facc15;
        background: #fffbeb;
    }}
    .stage2-timeline-event.bad .stage2-event-scores div {{
        border-color: #fca5a5;
        background: #fef2f2;
    }}
    .stage2-timeline-event.neutral .stage2-event-scores div {{
        border-color: #cbd5e1;
        background: #f8fafc;
    }}
    .stage2-event-scores span {{
        display: block;
        color: #64748b;
        font-size: 10px;
        margin-bottom: 4px;
    }}
    .stage2-event-scores strong {{
        color: #0f172a;
        font-size: 15px;
        line-height: 1.25;
    }}
    .stage2-event-note {{
        margin: 0 12px 10px;
        border: 1px solid #d6dee8;
        border-radius: 7px;
        background: #f8fafc;
        padding: 8px 10px;
        font-size: 12px;
        color: #334155;
        line-height: 1.4;
    }}
    .stage2-event-detail {{
        border-top: 1px solid #d6dee8;
        background: #fbfdff;
    }}
    .stage2-event-detail summary {{
        cursor: pointer;
        padding: 9px 12px;
        font-weight: 800;
        color: #0f172a;
        font-size: 12px;
        list-style-position: inside;
    }}
    .stage2-timeline-chat-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(320px, 1fr));
        gap: 12px;
        padding: 0 12px 12px;
    }}
    .stage2-panel {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #fff;
        overflow: hidden;
    }}
    .stage2-panel-title {{
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
        padding: 10px 12px;
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-pre {{
        margin: 0;
        padding: 13px 14px;
        min-height: 150px;
        max-height: 260px;
        overflow: auto;
        background: #fbfdfc;
        color: #020617;
        font-size: 12px;
        line-height: 1.55;
        white-space: pre-wrap;
        font-family: Consolas, "Courier New", monospace;
    }}
    .stage2-status {{
        display: inline-block;
        border: 1px solid #22c55e;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 800;
        white-space: nowrap;
    }}
    .stage2-status.warn {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    .stage2-status.bad {{
        border-color: #ef4444;
        background: #fef2f2;
        color: #991b1b;
    }}
    .stage2-status.neutral {{
        border-color: #94a3b8;
        background: #f8fafc;
        color: #334155;
    }}
    .stage2-change {{
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
        margin: 0 12px 12px;
    }}
    .stage2-change-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
        padding: 12px 14px;
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-change-main-title {{
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-change-inline {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .stage2-change-inline span {{
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        background: #ffffff;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 800;
        color: #334155;
        white-space: nowrap;
    }}
    .stage2-change-inline strong {{
        color: #0f172a;
    }}
    .stage2-change-summary {{
        display: grid;
        grid-template-columns: repeat(3, minmax(120px, 1fr));
        gap: 8px;
        padding: 10px 12px;
        background: #f8fafc;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-change-summary div {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #ffffff;
        padding: 8px 10px;
    }}
    .stage2-change-summary span {{
        display: block;
        font-size: 10px;
        color: #475569;
        margin-bottom: 3px;
    }}
    .stage2-change-summary strong {{
        font-size: 15px;
        color: #0f172a;
    }}
    .stage2-change-impact {{
        margin: 10px 12px 0;
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #f8fafc;
        padding: 8px 10px;
        font-size: 12px;
        color: #334155;
        font-weight: 700;
    }}
    .stage2-change-impact.good {{
        border-color: #86efac;
        background: #f0fdf4;
        color: #166534;
    }}
    .stage2-change-impact.neutral {{
        border-color: #cbd5e1;
        background: #f8fafc;
        color: #334155;
    }}
    .stage2-change-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
        padding: 12px;
    }}
    .stage2-change-box {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        overflow: hidden;
        background: #ffffff;
    }}
    .stage2-change-title {{
        padding: 8px 10px;
        background: #eef2f7;
        border-bottom: 1px solid #d6dee8;
        font-size: 12px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-change-table-wrap {{
        max-height: 220px;
        overflow-y: auto;
        overflow-x: hidden;
    }}
    .stage2-change-table {{
        width: 100%;
        min-width: 0;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 9px;
    }}
    .stage2-change-table th {{
        background: #e58d90;
        color: #000;
        border: 1px solid #111827;
        padding: 5px 4px;
        text-align: center;
        font-weight: 800;
        word-break: break-word;
    }}
    .stage2-change-table td {{
        background: #ffffff;
        border: 1px solid #111827;
        padding: 5px 4px;
        text-align: center;
        color: #000;
        word-break: break-word;
    }}
    .stage2-change-table tr.empty td {{ background: #fff4b8; }}
    .stage2-change-table tr.new td {{ background: #ecfdf3; }}
    .stage2-unit-status {{
        display: inline-block;
        border: 1px solid #94a3b8;
        border-radius: 999px;
        padding: 2px 6px;
        font-size: 9px;
        font-weight: 800;
        background: #f8fafc;
        color: #334155;
        white-space: nowrap;
    }}
    .stage2-unit-status.new {{
        border-color: #22c55e;
        background: #dcfce7;
        color: #166534;
    }}
    .stage2-unit-status.empty {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    @media (max-width: 980px) {{
        .stage2-order-timeline-head {{ flex-direction: column; }}
        .stage2-order-kicker {{ margin-left: 0; }}
        .stage2-order-pills {{ justify-content: flex-start; }}
        .stage2-evidence-grid {{ grid-template-columns: 1fr; }}
        .stage2-event-scores {{ grid-template-columns: 1fr; }}
        .stage2-timeline-chat-grid {{ grid-template-columns: 1fr; }}
        .stage2-change-grid {{ grid-template-columns: 1fr; }}
        .stage2-change-summary {{ grid-template-columns: 1fr; }}
    }}
    </style>
    <div class="stage2-timeline-audit">
        <div class="stage2-timeline-page-head">
            <div class="stage2-timeline-page-title">{escape(title)}</div>
        </div>
        {''.join(order_cards)}
    </div>
    """
    st.html(html)


def render_stage2_match_history(key_prefix: str, limit: int = 20) -> None:
    history = load_stage2_match_history(limit)
    if not history:
        return

    metrics = stage2_match_summary_metrics(history)
    body = []
    for idx, row in enumerate(history, start=1):
        created_at = str(row.get("created_at", "") or "")
        body.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{escape(created_at[:19])}</td>"
            f"<td>{escape(str(row.get('candidate_summary', '') or '-'))}</td>"
            f"<td>{pct_text(float(row.get('p_match', 0.0) or 0.0))}</td>"
            f"<td>{escape(str(row.get('incoming_complete_units', 0) or 0))}</td>"
            f"<td>{escape(str(row.get('duplicate_units', 0) or 0))}</td>"
            f"<td>{escape(str(row.get('proposed_fill_count', 0) or 0))}</td>"
            f"<td>{escape(str(row.get('policy_reason', '') or '-'))}</td>"
            "</tr>"
        )

    html = f"""
    <style>
    .stage2-history {{
        margin-top: 16px;
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
        font-family: Arial, Helvetica, sans-serif;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
    }}
    .stage2-history-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 12px 14px;
        background: #f8fafc;
        border-bottom: 1px solid #d6dee8;
    }}
    .stage2-history-title {{
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
    }}
    .stage2-history-subtitle {{
        margin-top: 4px;
        font-size: 11px;
        color: #475569;
    }}
    .stage2-history-pills {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }}
    .stage2-history-pills span {{
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #fff;
        padding: 6px 9px;
        font-size: 11px;
        font-weight: 700;
        color: #111827;
    }}
    .stage2-history-scroll {{
        max-height: 360px;
        overflow: auto;
        padding: 12px 14px 14px;
        background: #eef2f7;
    }}
    .stage2-history-table-wrap {{
        overflow-x: auto;
        border: 1px solid #111827;
        background: #fff;
    }}
    .stage2-history-table {{
        width: 100%;
        min-width: 1080px;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 11px;
    }}
    .stage2-history-table th {{
        background: #e58d90;
        color: #000;
        border: 1px solid #111827;
        padding: 8px 7px;
        text-align: center;
        font-weight: 800;
    }}
    .stage2-history-table td {{
        border: 1px solid #111827;
        padding: 7px;
        background: #fff;
        vertical-align: top;
        color: #000;
        word-break: break-word;
    }}
    .stage2-history-table td:nth-child(3),
    .stage2-history-table td:nth-child(8) {{
        text-align: left;
    }}
    .stage2-history-table td:not(:nth-child(3)):not(:nth-child(8)) {{
        text-align: center;
    }}
    .stage2-history-status {{
        display: inline-block;
        border: 1px solid #22c55e;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 800;
        white-space: nowrap;
    }}
    .stage2-history-status.warn {{
        border-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }}
    .stage2-history-status.bad {{
        border-color: #ef4444;
        background: #fef2f2;
        color: #991b1b;
    }}
    .stage2-history-status.neutral {{
        border-color: #94a3b8;
        background: #f8fafc;
        color: #334155;
    }}
    @media (max-width: 980px) {{
        .stage2-history-head {{ align-items: flex-start; flex-direction: column; }}
        .stage2-history-pills {{ justify-content: flex-start; }}
    }}
    </style>
    <section class="stage2-history">
        <div class="stage2-history-head">
            <div>
                <div class="stage2-history-title">Riwayat batch pencocokan</div>
                <div class="stage2-history-subtitle">
                    Audit keputusan matcher untuk batch susulan yang sudah pernah diproses.
                </div>
            </div>
            <div class="stage2-history-pills">
                <span>Total audit {escape(str(metrics['total']))}</span>
                <span>Avg P_MATCH {pct_text(float(metrics['avg_match']))}</span>
                <span>Cek manual {escape(str(metrics['review']))}</span>
                <span>Duplikat {escape(str(metrics['duplicate']))}</span>
            </div>
        </div>
        <div class="stage2-history-scroll">
            <div class="stage2-history-table-wrap">
                <table class="stage2-history-table">
                    <thead>
                        <tr>
                            <th style="width:48px">No.</th>
                            <th style="width:150px">Waktu</th>
                            <th style="width:250px">Kandidat order</th>
                            <th style="width:90px">P_MATCH</th>
                            <th style="width:95px">Unit masuk</th>
                            <th style="width:90px">Duplikat</th>
                            <th style="width:90px">Isi slot</th>
                            <th>Alasan</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(body)}</tbody>
                </table>
            </div>
        </div>
    </section>
    """
    st.html(html)


def rows_from_new_order_text(tokenizer, model, device, raw_text: str, max_seq_len: int) -> tuple[pd.DataFrame, List[Dict[str, object]]]:
    chunks = split_new_order_messages(raw_text)
    rows = []
    audits = []

    for chunk_index, chunk in enumerate(chunks, start=1):
        ner_text = prepare_text_for_ner(chunk)
        spans = ner_predict_spans_with_scores(tokenizer, model, device, ner_text, max_seq_len)
        values = group_spans(spans)
        qty = qty_from_ner(values)
        ro_date = joined_values(values, "RO_DATE") or first_value(values, "RO_DATE")
        ro_date = repair_ro_date_from_header(ro_date, chunk)
        pickup_common = common_order_value(values, "ORIGIN")
        destination_common = common_order_value(values, "DESTINATION")
        truck_type = first_value(values, "UNIT_TYPE")
        loading_values = loading_values_from_spans(spans)
        last_valid_pickup = ""

        for unit_index in range(qty):
            loading_explicit_for_unit = unit_index < len(loading_values)
            raw_loading_value = indexed_loading_value(loading_values, values, unit_index)
            if qty == 1:
                driver = " / ".join(values.get("DRIVER", []))
            else:
                driver = indexed_value(values, "DRIVER", unit_index)
            plate = indexed_value(values, "PLATE", unit_index)
            phone = indexed_value(values, "PHONE", unit_index)
            if is_sender_name_noise_driver(driver, plate, phone):
                driver = ""
            pickup = indexed_value(values, "ORIGIN", unit_index, pickup_common)
            pickup_noise_for_empty_unit = should_inherit_previous_pickup_for_empty_unit(
                pickup,
                driver,
                plate,
                phone,
            )
            if pickup_noise_for_empty_unit and filled_value(last_valid_pickup):
                pickup = last_valid_pickup
            elif filled_value(pickup) and not is_short_noise_pickup_token(pickup):
                last_valid_pickup = pickup
            destination = indexed_value(values, "DESTINATION", unit_index, destination_common)
            unit_complete = all(filled_value(value) for value in (driver, plate, phone))
            if not unit_complete:
                if not loading_explicit_for_unit:
                    raw_loading_value = ""
            rows.append(
                {
                    "No.": len(rows) + 1,
                    "Tgl RO": ro_date,
                    "Tgl Muat": raw_loading_value,
                    "Pickup": pickup,
                    "Tujuan": destination,
                    "No. Plat": plate,
                    "Type Truck": truck_type,
                    "Driver": driver,
                    "Kontak Driver": phone,
                    "_raw_tgl_muat": raw_loading_value,
                    "_chunk": chunk_index,
                    "_qty_ner": qty,
                    "_source": chunk,
                    "_ner_input": ner_text,
                }
            )

        audits.append(
            {
                "chunk": chunk_index,
                "qty_ner": qty,
                "spans": spans,
                "source": chunk,
                "ner_input": ner_text,
                "labels": {key: values.get(key, []) for key in sorted(values)},
            }
        )

    return pd.DataFrame(rows), audits


def cumulative_rows_and_audits_from_raw_chats(
    tokenizer,
    model,
    device,
    raw_chats: Sequence[object],
    max_seq_len: int,
    normalized: bool,
) -> tuple[pd.DataFrame, List[Dict[str, object]]]:
    normalized = bool(normalized and OPERATIONAL_NORMALIZATION_ENABLED)
    all_frames: List[pd.DataFrame] = []
    all_audits: List[Dict[str, object]] = []
    chunk_offset = 0
    row_offset = 0

    for batch_index, raw_chat in enumerate(raw_chats, start=1):
        if isinstance(raw_chat, dict):
            raw_chat_text = str(raw_chat.get("chat_text", "") or "").strip()
            batch_created_at = str(raw_chat.get("created_at", "") or "").strip()
            batch_id = str(raw_chat.get("id", "") or "").strip()
        else:
            raw_chat_text = str(raw_chat or "").strip()
            batch_created_at = ""
            batch_id = ""
        if not raw_chat_text:
            continue

        batch_time = batch_created_at.replace("T", " ")[:19]
        batch_label = f"Batch {batch_index}"
        if batch_time:
            batch_label = f"{batch_label} - {batch_time}"

        batch_df, batch_audits = rows_from_new_order_text(
            tokenizer,
            model,
            device,
            raw_chat_text,
            max_seq_len,
        )
        if normalized and not batch_df.empty:
            batch_df = normalize_operational_excel(batch_df)

        if not batch_df.empty:
            batch_df = batch_df.copy()
            batch_df["_chunk"] = batch_df["_chunk"].astype(int) + chunk_offset
            batch_df["_batch_index"] = batch_index
            batch_df["_batch_label"] = batch_label
            batch_df["_batch_created_at"] = batch_created_at
            batch_df["_batch_id"] = batch_id
            batch_df["No."] = range(row_offset + 1, row_offset + len(batch_df) + 1)
            all_frames.append(batch_df)
            row_offset += len(batch_df)

        for audit in batch_audits:
            adjusted = dict(audit)
            adjusted["chunk"] = int(adjusted.get("chunk", 0) or 0) + chunk_offset
            adjusted["batch_index"] = batch_index
            adjusted["batch_label"] = batch_label
            adjusted["batch_created_at"] = batch_created_at
            adjusted["batch_id"] = batch_id
            all_audits.append(adjusted)

        chunk_offset += len(batch_audits)

    if all_frames:
        return pd.concat(all_frames, ignore_index=True), all_audits
    return pd.DataFrame(columns=EXCEL_COLUMNS), all_audits


def render_excel_like_table(df: pd.DataFrame, height: int = 620) -> None:
    source_df = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    visible = source_df[[col for col in EXCEL_COLUMNS if col in source_df.columns]].copy()
    widths = {
        "No.": "50px",
        "Tgl RO": "115px",
        "Tgl Muat": "115px",
        "Pickup": "180px",
        "Tujuan": "360px",
        "No. Plat": "105px",
        "Type Truck": "105px",
        "Driver": "125px",
        "Kontak Driver": "130px",
    }
    header_cells = []
    for col in visible.columns:
        header_cells.append(
            f'<th style="width:{widths.get(col, "120px")}">'
            f'<span>{escape(col)}</span><span class="xl-filter"></span></th>'
        )

    body_rows = []
    for idx, row in visible.iterrows():
        row_class = " class='partial-row'" if is_partial_visual_row(source_df.loc[idx]) else ""
        cells = []
        for col in visible.columns:
            value = escape(str(row.get(col, "") if pd.notna(row.get(col, "")) else ""))
            cells.append(f"<td>{value}</td>")
        body_rows.append(f"<tr{row_class}>" + "".join(cells) + "</tr>")

    html = f"""
    <style>
    .excel-wrap {{
        width: 100%;
        height: {height}px;
        overflow: auto;
        border: 1px solid #111;
        background: #ffffff;
        font-family: Arial, Helvetica, sans-serif;
    }}
    table.excel {{
        border-collapse: collapse;
        table-layout: fixed;
        width: max-content;
        min-width: 100%;
        font-size: 11px;
        color: #000;
    }}
    table.excel th {{
        position: sticky;
        top: 0;
        z-index: 2;
        height: 34px;
        padding: 0 20px 0 6px;
        border: 1px solid #111;
        background: #e89393;
        text-align: center;
        font-weight: 700;
        white-space: nowrap;
    }}
    table.excel td {{
        height: 20px;
        padding: 1px 5px;
        border: 1px solid #111;
        text-align: center;
        vertical-align: middle;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        background: #fff;
    }}
    table.excel tr:nth-child(even) td {{
        background: #fcfcfc;
    }}
    table.excel tr.partial-row td,
    table.excel tr.partial-row:nth-child(even) td {{
        background: #fff3b0;
    }}
    table.excel td:nth-child(5) {{
        text-align: center;
    }}
    .xl-filter {{
        position: absolute;
        right: 6px;
        top: 50%;
        width: 11px;
        height: 11px;
        transform: translateY(-50%);
    }}
    .xl-filter:before {{
        content: "";
        position: absolute;
        left: 1px;
        top: 2px;
        width: 9px;
        height: 1px;
        background: #111;
        box-shadow: 0 3px 0 #111;
    }}
    .xl-filter:after {{
        content: "";
        position: absolute;
        left: 4px;
        top: 7px;
        width: 0;
        height: 0;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 4px solid #111;
    }}
    </style>
    <div class="excel-wrap">
        <table class="excel">
            <thead><tr>{''.join(header_cells)}</tr></thead>
            <tbody>{''.join(body_rows)}</tbody>
        </table>
    </div>
    """
    st.html(html)


NER_EVAL_ATTRIBUTES = [
    ("UNIT_QTY", "Qty Unit", ["UNIT_QTY"], None),
    ("RO_DATE", "Tgl RO", ["RO_DATE"], "Tgl RO"),
    ("LOAD_DATE", "Tgl Muat", ["LOAD_DATE", "TIME"], "Tgl Muat"),
    ("ORIGIN", "Pickup", ["ORIGIN"], "Pickup"),
    ("DESTINATION", "Tujuan", ["DESTINATION"], "Tujuan"),
    ("PLATE", "No. Plat", ["PLATE"], "No. Plat"),
    ("UNIT_TYPE", "Type Truck", ["UNIT_TYPE"], "Type Truck"),
    ("DRIVER", "Driver", ["DRIVER"], "Driver"),
    ("PHONE", "Kontak Driver", ["PHONE"], "Kontak Driver"),
]


def span_values_for_labels(spans: Sequence[Dict[str, object]], labels: Sequence[str]) -> List[str]:
    values = []
    label_set = set(labels)
    for span in spans:
        if str(span.get("label", "")) not in label_set:
            continue
        value = clean_cell_value(str(span.get("value", "")))
        if value:
            values.append(value)
    return values


def span_confidence_for_labels(spans: Sequence[Dict[str, object]], labels: Sequence[str]) -> float:
    scores = []
    label_set = set(labels)
    for span in spans:
        if str(span.get("label", "")) not in label_set:
            continue
        try:
            scores.append(float(span.get("confidence", 0.0)))
        except Exception:
            pass
    return sum(scores) / len(scores) if scores else 0.0


def unique_nonblank(values: Iterable) -> List[str]:
    out = []
    for value in values:
        text = str(value or "").strip()
        if not filled_value(text):
            continue
        if text not in out:
            out.append(text)
    return out


def unique_clean_values(values: Iterable) -> List[str]:
    out = []
    seen = set()
    for value in values:
        text = clean_cell_value(str(value or ""))
        if not filled_value(text):
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def values_context_match(attr_key: str, ner_values: Sequence[str], output_values: Sequence[str]) -> bool:
    ner_clean = unique_clean_values(ner_values)
    output_clean = unique_clean_values(output_values)
    if not ner_clean or not output_clean:
        return False

    if attr_key == "UNIT_QTY":
        qty_digits = {digit for value in ner_clean for digit in re.findall(r"\d{1,3}", value)}
        return bool(qty_digits) and any(
            any(digit in value for digit in qty_digits) for value in output_clean
        )

    ner_set = {value.casefold() for value in ner_clean}
    output_set = {value.casefold() for value in output_clean}
    return output_set.issubset(ner_set) or ner_set.issubset(output_set)


def contextual_attribute_confidence(
    attr_key: str,
    attr_name: str,
    ner_values: Sequence[str],
    output_values: Sequence[str],
    raw_confidence: float,
) -> float:
    if not values_context_match(attr_key, ner_values, output_values):
        return raw_confidence

    has_red_issue = any(attr_value_needs_red_border(attr_name, value) for value in ner_values)
    has_red_issue = has_red_issue or any(
        attr_value_needs_red_border(attr_name, value) for value in output_values
    )
    if has_red_issue:
        return raw_confidence

    return max(raw_confidence, 0.95)


NER_CONFIDENCE_AUDIT_THRESHOLD = 0.90


def confidence_bucket(score: float, captured: bool) -> str:
    if not captured:
        return "MISSING"
    if score >= 0.90:
        return "HIGH"
    if score >= 0.70:
        return "MEDIUM"
    return "LOW"


def build_ner_block_evaluation(
    excel_df: pd.DataFrame,
    audits: Sequence[Dict[str, object]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    detail_rows = []

    if excel_df is None:
        excel_df = pd.DataFrame()

    for audit in audits:
        chunk_id = int(audit.get("chunk", 0) or 0)
        spans = audit.get("spans", [])
        if not isinstance(spans, list):
            spans = []

        block_rows = (
            excel_df[excel_df["_chunk"] == chunk_id].copy()
            if "_chunk" in excel_df.columns
            else pd.DataFrame()
        )
        captured_count = 0
        confidence_values = []
        missing_attrs = []
        low_attrs = []

        for _, attr_name, labels, output_col in NER_EVAL_ATTRIBUTES:
            ner_values = span_values_for_labels(spans, labels)
            output_values = (
                unique_nonblank(block_rows[output_col].tolist())
                if output_col and output_col in block_rows.columns
                else [str(audit.get("qty_ner", ""))]
            )
            captured = bool(ner_values)
            confidence = span_confidence_for_labels(spans, labels)
            bucket = confidence_bucket(confidence, captured)
            if captured:
                captured_count += 1
                confidence_values.append(confidence)
            else:
                missing_attrs.append(attr_name)
            if bucket == "LOW":
                low_attrs.append(attr_name)

            if captured and output_values:
                status = "OK"
            elif captured and not output_values:
                status = "CAPTURED_NO_OUTPUT"
            else:
                status = "MISSING"

            detail_rows.append(
                {
                    "chunk": chunk_id,
                    "attribute": attr_name,
                    "ner_label": "+".join(labels),
                    "ner_captured": " | ".join(ner_values),
                    "output_table": " | ".join(output_values),
                    "confidence": confidence,
                    "bucket": bucket,
                    "status": status,
                }
            )

        total_attrs = len(NER_EVAL_ATTRIBUTES)
        completeness = captured_count / total_attrs if total_attrs else 0.0
        avg_conf = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        quality = (0.55 * completeness) + (0.45 * avg_conf)
        summary_rows.append(
            {
                "chunk": chunk_id,
                "qty_ner": audit.get("qty_ner", ""),
                "output_rows": len(block_rows),
                "captured": f"{captured_count}/{total_attrs}",
                "completeness": completeness,
                "avg_confidence": avg_conf,
                "quality_score": quality,
                "missing": ", ".join(missing_attrs) if missing_attrs else "-",
                "low_confidence": ", ".join(low_attrs) if low_attrs else "-",
                "source_preview": re.sub(r"\s+", " ", str(audit.get("ner_input", ""))).strip()[:180],
            }
        )

    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def render_ner_evaluation_html(
    summary_df: pd.DataFrame,
    detail_df: pd.DataFrame,
    height: int = 560,
) -> None:
    def pct(value) -> str:
        try:
            return f"{float(value) * 100:.1f}%"
        except Exception:
            return "0.0%"

    summary_rows = []
    for _, row in summary_df.iterrows():
        quality = float(row.get("quality_score", 0.0) or 0.0)
        row_class = "good" if quality >= 0.85 else "warn" if quality >= 0.65 else "bad"
        summary_rows.append(
            f"<tr class='{row_class}'>"
            f"<td>{escape(str(row.get('chunk', '')))}</td>"
            f"<td>{escape(str(row.get('qty_ner', '')))}</td>"
            f"<td>{escape(str(row.get('output_rows', '')))}</td>"
            f"<td>{escape(str(row.get('captured', '')))}</td>"
            f"<td>{pct(row.get('completeness', 0.0))}</td>"
            f"<td>{pct(row.get('avg_confidence', 0.0))}</td>"
            f"<td>{pct(row.get('quality_score', 0.0))}</td>"
            f"<td>{escape(str(row.get('missing', '')))}</td>"
            f"<td>{escape(str(row.get('low_confidence', '')))}</td>"
            f"<td>{escape(str(row.get('source_preview', '')))}</td>"
            "</tr>"
        )

    detail_rows = []
    for _, row in detail_df.iterrows():
        bucket = str(row.get("bucket", "MISSING"))
        detail_rows.append(
            f"<tr class='{escape(bucket.lower())}'>"
            f"<td>{escape(str(row.get('chunk', '')))}</td>"
            f"<td>{escape(str(row.get('attribute', '')))}</td>"
            f"<td>{escape(str(row.get('ner_label', '')))}</td>"
            f"<td>{escape(str(row.get('ner_captured', '')))}</td>"
            f"<td>{escape(str(row.get('output_table', '')))}</td>"
            f"<td>{pct(row.get('confidence', 0.0))}</td>"
            f"<td>{escape(bucket)}</td>"
            f"<td>{escape(str(row.get('status', '')))}</td>"
            "</tr>"
        )

    html = f"""
    <style>
    .ner-eval-wrap {{
        height: {height}px;
        overflow: auto;
        border: 1px solid #111;
        background: #fff;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .ner-eval-section {{
        min-width: 1280px;
        padding-bottom: 14px;
    }}
    .ner-eval-title {{
        position: sticky;
        top: 0;
        z-index: 4;
        background: #f8fafc;
        border-bottom: 1px solid #111;
        padding: 8px 10px;
        font-weight: 700;
        font-size: 12px;
    }}
    table.ner-eval {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 11px;
    }}
    table.ner-eval th {{
        position: sticky;
        top: 31px;
        z-index: 3;
        background: #e89393;
        color: #000;
        border: 1px solid #111;
        padding: 6px 5px;
        text-align: center;
        font-weight: 700;
        white-space: nowrap;
    }}
    table.ner-eval td {{
        border: 1px solid #111;
        padding: 4px 5px;
        vertical-align: top;
        background: #fff;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    table.ner-eval tr.good td,
    table.ner-eval tr.high td {{ background: #ecfdf5; }}
    table.ner-eval tr.warn td,
    table.ner-eval tr.medium td {{ background: #fffbeb; }}
    table.ner-eval tr.bad td,
    table.ner-eval tr.low td,
    table.ner-eval tr.missing td {{ background: #fee2e2; }}
    .ner-eval-subtitle {{
        padding: 10px 8px 5px 8px;
        font-weight: 700;
        font-size: 12px;
        background: #fff;
    }}
    </style>
    <div class="ner-eval-wrap">
      <div class="ner-eval-section">
        <div class="ner-eval-title">Evaluasi IndoBERT NER per blok chat</div>
        <div class="ner-eval-subtitle">Ringkasan blok</div>
        <table class="ner-eval">
          <thead>
            <tr>
              <th style="width:55px">Chunk</th>
              <th style="width:70px">Qty NER</th>
              <th style="width:80px">Rows</th>
              <th style="width:90px">Captured</th>
              <th style="width:95px">Completeness</th>
              <th style="width:105px">Avg Conf</th>
              <th style="width:105px">Quality</th>
              <th style="width:190px">Missing</th>
              <th style="width:160px">Low Conf</th>
              <th>Original Block Preview</th>
            </tr>
          </thead>
          <tbody>{''.join(summary_rows)}</tbody>
        </table>
        <div class="ner-eval-subtitle">Detail atribut</div>
        <table class="ner-eval">
          <thead>
            <tr>
              <th style="width:55px">Chunk</th>
              <th style="width:120px">Atribut</th>
              <th style="width:125px">NER Label</th>
              <th>Yang Ditangkap NER</th>
              <th>Output Tabel</th>
              <th style="width:95px">Confidence</th>
              <th style="width:85px">Indicator</th>
              <th style="width:130px">Status</th>
            </tr>
          </thead>
          <tbody>{''.join(detail_rows)}</tbody>
        </table>
      </div>
    </div>
    """
    st.html(html)


def pct_text(value: float) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except Exception:
        return "0.0%"


def output_values_for_attribute(
    block_rows: pd.DataFrame,
    audit: Dict[str, object],
    attr_key: str,
    output_col: str | None,
) -> List[str]:
    if attr_key == "UNIT_QTY":
        qty = str(audit.get("qty_ner", "") or "").strip()
        rows_count = len(block_rows)
        values = []
        if qty:
            values.append(f"QTY NER {qty}")
        if rows_count:
            values.append(f"OUTPUT {rows_count} BARIS")
        return values

    if not output_col or output_col not in block_rows.columns:
        return []
    return unique_nonblank(block_rows[output_col].tolist())


def block_unit_completion(block_rows: pd.DataFrame) -> tuple[int, int, str]:
    if block_rows is None or block_rows.empty:
        return 0, 0, "BELUM LENGKAP"

    complete_count = 0
    for _, row in block_rows.iterrows():
        has_driver = filled_value(str(row.get("Driver", "") or ""))
        has_plate = filled_value(str(row.get("No. Plat", "") or ""))
        has_phone = filled_value(str(row.get("Kontak Driver", "") or ""))
        if has_driver and has_plate and has_phone:
            complete_count += 1

    total = len(block_rows)
    status = "LENGKAP" if total > 0 and complete_count == total else "BELUM LENGKAP"
    return complete_count, total, status


def output_cell_key(row_index: int, col: str) -> str:
    return f"{row_index}::{col}"


def red_output_cell_keys_for_missing_attribute(
    rows: Sequence[Dict[str, object]],
    output_col: str | None,
) -> set[str]:
    if not output_col:
        return set()

    keys: set[str] = set()
    identity_peers = {
        "Driver": ("No. Plat", "Kontak Driver"),
        "No. Plat": ("Driver", "Kontak Driver"),
        "Kontak Driver": ("Driver", "No. Plat"),
    }

    if output_col in identity_peers:
        for idx, row in enumerate(rows):
            current_value = str(row.get(output_col, "") or "")
            if filled_value(current_value):
                continue
            if any(filled_value(str(row.get(peer, "") or "")) for peer in identity_peers[output_col]):
                keys.add(output_cell_key(idx, output_col))
        return keys

    if output_col == "Tgl Muat":
        for idx, row in enumerate(rows):
            current_value = str(row.get(output_col, "") or "")
            if filled_value(current_value):
                continue
            has_unit_identity = any(
                filled_value(str(row.get(peer, "") or ""))
                for peer in ("Driver", "No. Plat", "Kontak Driver")
            )
            if has_unit_identity:
                keys.add(output_cell_key(idx, output_col))
        return keys

    for idx, row in enumerate(rows):
        if not filled_value(str(row.get(output_col, "") or "")):
            keys.add(output_cell_key(idx, output_col))
    return keys


def build_simple_ner_eval_cards(
    excel_df: pd.DataFrame,
    audits: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    if excel_df is None:
        excel_df = pd.DataFrame()

    cards: List[Dict[str, object]] = []
    for audit in audits:
        chunk_id = int(audit.get("chunk", 0) or 0)
        spans = audit.get("spans", [])
        if not isinstance(spans, list):
            spans = []

        block_rows = (
            excel_df[excel_df["_chunk"] == chunk_id].copy()
            if "_chunk" in excel_df.columns
            else pd.DataFrame()
        )
        visible_rows = (
            block_rows[[col for col in EXCEL_COLUMNS if col in block_rows.columns]]
            .fillna("")
            .to_dict("records")
            if not block_rows.empty
            else []
        )

        attr_rows = []
        captured_count = 0
        ok_count = 0
        needs_check_count = 0
        low_confidence_count = 0
        low_confidence_attrs = []
        red_output_columns = set()
        red_output_cells = set()
        problem_attrs = set()
        confidence_values = []
        grouped_loading_values = loading_values_from_spans(spans)
        output_attr_map = {
            output_col: attr_name
            for _, attr_name, _, output_col in NER_EVAL_ATTRIBUTES
            if output_col
        }
        for attr_key, attr_name, labels, output_col in NER_EVAL_ATTRIBUTES:
            raw_ner_values = (
                grouped_loading_values
                if attr_key == "LOAD_DATE"
                else span_values_for_labels(spans, labels)
            )
            ner_values = unique_clean_values(raw_ner_values)
            output_values = output_values_for_attribute(block_rows, audit, attr_key, output_col)
            captured = bool(ner_values)
            has_output = bool(output_values)
            raw_confidence = span_confidence_for_labels(spans, labels)
            confidence = contextual_attribute_confidence(
                attr_key,
                attr_name,
                ner_values,
                output_values,
                raw_confidence,
            )
            low_confidence = captured and confidence < NER_CONFIDENCE_AUDIT_THRESHOLD

            if captured:
                captured_count += 1
                confidence_values.append(confidence)

            needs_check = False
            if captured and has_output:
                status = "OK"
                status_class = "ok"
                ok_count += 1
            elif captured and not has_output:
                status = "NER ADA, OUTPUT KOSONG"
                status_class = "warn"
                needs_check = True
            elif not captured and has_output:
                status = "OUTPUT ADA, CEK NER"
                status_class = "warn"
                needs_check = True
            else:
                status = "BELUM TERBACA"
                status_class = "miss"
                needs_check = True

            if output_col and needs_check and not has_output:
                missing_cells = red_output_cell_keys_for_missing_attribute(visible_rows, output_col)
                if missing_cells:
                    red_output_cells.update(missing_cells)
                elif output_col not in {"Driver", "No. Plat", "Kontak Driver", "Tgl Muat"}:
                    red_output_columns.add(output_col)

            if low_confidence:
                low_confidence_count += 1
                low_confidence_attrs.append(attr_name)
            if needs_check:
                needs_check_count += 1
                problem_attrs.add(attr_name)
            if any(attr_value_needs_red_border(attr_name, value) for value in ner_values):
                problem_attrs.add(attr_name)

            attr_rows.append(
                {
                    "attribute": attr_name,
                    "ner_value_items": ner_values,
                    "ner_values": " | ".join(ner_values) if ner_values else "-",
                    "output_values": " | ".join(output_values) if output_values else "-",
                    "confidence": confidence,
                    "confidence_bucket": confidence_bucket(confidence, captured),
                    "status": status,
                    "status_class": status_class,
                }
            )

        for row in visible_rows:
            for col in EXCEL_COLUMNS:
                if cell_needs_red_border(row, col):
                    problem_attrs.add(output_attr_map.get(col, col))
        for col in red_output_columns:
            problem_attrs.add(output_attr_map.get(col, col))
        for cell_key in red_output_cells:
            _, col = cell_key.split("::", 1)
            problem_attrs.add(output_attr_map.get(col, col))

        total_attrs = len(NER_EVAL_ATTRIBUTES)
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        complete_units, total_units, order_status = block_unit_completion(block_rows)
        cards.append(
            {
                "chunk": chunk_id,
                "batch_index": int(audit.get("batch_index", 0) or 0),
                "batch_label": str(audit.get("batch_label", "") or ""),
                "batch_created_at": str(audit.get("batch_created_at", "") or ""),
                "batch_id": str(audit.get("batch_id", "") or ""),
                "source": str(audit.get("source", "") or ""),
                "ner_input": str(audit.get("ner_input", "") or ""),
                "rows_count": len(block_rows),
                "output_rows": visible_rows,
                "complete_units": complete_units,
                "total_units": total_units,
                "order_status": order_status,
                "captured_count": captured_count,
                "ok_count": ok_count,
                "total_attrs": total_attrs,
                "avg_confidence": avg_confidence,
                "needs_check": needs_check_count,
                "low_confidence_count": low_confidence_count,
                "low_confidence_attrs": low_confidence_attrs,
                "red_output_columns": sorted(red_output_columns),
                "red_output_cells": sorted(red_output_cells),
                "problem_count": len(problem_attrs),
                "problem_attrs": sorted(problem_attrs),
                "attr_rows": attr_rows,
            }
        )

    return cards


def ner_eval_card_identity(card: Dict[str, object]) -> str:
    source_key = stage2_norm_key(str(card.get("source", "") or ""))
    return "|".join(
        [
            str(card.get("batch_id", "") or ""),
            str(card.get("batch_index", "") or ""),
            str(card.get("chunk", "") or ""),
            source_key[:80],
        ]
    )


def build_ner_stage2_card_groups(
    cards: Sequence[Dict[str, object]],
    match_history: Sequence[Dict[str, object]] | None,
) -> List[Dict[str, object]]:
    if not cards or not match_history:
        return []

    by_source: Dict[str, List[Dict[str, object]]] = {}
    for card in cards:
        source_key = stage2_norm_key(str(card.get("source", "") or ""))
        if source_key:
            by_source.setdefault(source_key, []).append(card)

    groups: List[Dict[str, object]] = []
    used_group_keys: set[str] = set()
    events = [
        event
        for event in stage2_top_events_from_history(match_history)
        if stage2_is_confident_match_merge(event)
    ]
    for group_index, timeline_group in enumerate(stage2_order_timeline_groups_from_events(events), start=1):
        stage_cards: List[Dict[str, object]] = []
        seen_card_ids: set[str] = set()
        for event in timeline_group.get("events", []):
            for text in (
                resolve_stage2_candidate_chat_text(event),
                str(event.get("incoming_text", "") or ""),
            ):
                text_key = stage2_norm_key(text)
                for card in by_source.get(text_key, []):
                    card_id = ner_eval_card_identity(card)
                    if card_id not in seen_card_ids:
                        seen_card_ids.add(card_id)
                        stage_cards.append(card)

        if len(stage_cards) < 2:
            continue

        group_key = str(timeline_group.get("key", "") or "")
        if group_key in used_group_keys:
            continue
        used_group_keys.add(group_key)
        groups.append(
            {
                "index": group_index,
                "key": group_key,
                "summary": str(timeline_group.get("summary", "") or "Order gabungan"),
                "latest_created_at": str(timeline_group.get("latest_created_at", "") or ""),
                "cards": stage_cards,
                "card_ids": [ner_eval_card_identity(card) for card in stage_cards],
            }
        )
    return groups


def render_simple_ner_block_evaluation(
    cards: Sequence[Dict[str, object]],
    height: int = 760,
    grouped_orders: Sequence[Dict[str, object]] | None = None,
    max_items: int | None = None,
) -> None:
    if not cards:
        st.info("Belum ada blok chat untuk dievaluasi.")
        return

    widths = {
        "No.": "46px",
        "Tgl RO": "100px",
        "Tgl Muat": "100px",
        "Pickup": "145px",
        "Tujuan": "220px",
        "No. Plat": "95px",
        "Type Truck": "90px",
        "Driver": "120px",
        "Kontak Driver": "120px",
    }

    def output_table_html(
        rows: Sequence[Dict[str, object]],
        red_output_columns: Sequence[str] | None = None,
        red_output_cells: Sequence[str] | None = None,
    ) -> str:
        if not rows:
            return "<div class='empty-output'>Tidak ada output tabel untuk blok ini.</div>"
        red_column_set = set(red_output_columns or [])
        red_cell_set = set(red_output_cells or [])
        header = "".join(
            f"<th style='width:{widths.get(col, '110px')}'>{escape(col)}</th>"
            for col in EXCEL_COLUMNS
        )
        body = []
        for row_index, row in enumerate(rows):
            row_class = " class='partial-row'" if is_partial_visual_row(row) else ""
            cells = []
            for col in EXCEL_COLUMNS:
                value = row.get(col, "")
                value_text = str(value if value is not None else "")
                red_missing_value = (
                    (col in red_column_set or output_cell_key(row_index, col) in red_cell_set)
                    and not filled_value(value_text)
                )
                cell_class = (
                    " class='red-border-cell'"
                    if cell_needs_red_border(row, col) or red_missing_value
                    else ""
                )
                cells.append(f"<td{cell_class}>{escape(value_text)}</td>")
            body.append(f"<tr{row_class}>" + "".join(cells) + "</tr>")
        return (
            "<div class='mini-table-wrap'>"
            "<table class='mini-excel'>"
            f"<thead><tr>{header}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody>"
            "</table>"
            "</div>"
        )

    def attr_table_html(rows: Sequence[Dict[str, object]]) -> str:
        def ner_values_cell_html(row: Dict[str, object]) -> str:
            attribute = str(row.get("attribute", "") or "")
            items_raw = row.get("ner_value_items", [])
            items = [
                clean_cell_value(str(item))
                for item in items_raw
                if clean_cell_value(str(item))
            ] if isinstance(items_raw, list) else []
            if not items:
                fallback = clean_cell_value(str(row.get("ner_values", "")))
                missing_value = not filled_value(fallback) or fallback == "-"
                value_class = (
                    " red-border-value"
                    if attr_value_needs_red_border(attribute, fallback) or missing_value
                    else ""
                )
                return f"<span class='ner-single-value{value_class}'>{escape(fallback or '-')}</span>"
            if len(items) == 1:
                value_class = " red-border-value" if attr_value_needs_red_border(attribute, items[0]) else ""
                return f"<span class='ner-single-value{value_class}'>{escape(items[0])}</span>"
            cells = "".join(
                f"<span class='{'red-border-value' if attr_value_needs_red_border(attribute, item) else ''}'>{escape(item)}</span>"
                for item in items
            )
            return (
                "<div class='ner-value-grid' "
                f"style='grid-template-columns: repeat({len(items)}, minmax(80px, 1fr));'>"
                f"{cells}</div>"
            )

        body = []
        for row in rows:
            cls = escape(str(row.get("status_class", "")))
            body.append(
                f"<tr class='{cls}'>"
                f"<td>{escape(str(row.get('attribute', '')))}</td>"
                f"<td class='ner-values-cell'>{ner_values_cell_html(row)}</td>"
                f"<td>{pct_text(float(row.get('confidence', 0.0) or 0.0))}</td>"
                "</tr>"
            )
        return (
            "<table class='attr-check'>"
            "<thead><tr>"
            "<th>Atribut</th><th>Yang ditangkap Model</th>"
            "<th>Confidence</th>"
            "</tr></thead>"
            f"<tbody>{''.join(body)}</tbody>"
            "</table>"
        )

    def block_stage_html(card: Dict[str, object], stage_label: str | None = None) -> str:
        avg_conf = float(card.get("avg_confidence", 0.0) or 0.0)
        problem_count = int(card.get("problem_count", card.get("needs_check", 0)) or 0)
        quality_class = "good" if problem_count == 0 else "warn" if avg_conf >= 0.70 else "bad"
        batch_label = str(card.get("batch_label", "") or "")
        order_status = str(card.get("order_status", "BELUM LENGKAP") or "BELUM LENGKAP")
        status_class = "complete" if order_status == "LENGKAP" else "incomplete"
        unit_summary = (
            f"{int(card.get('complete_units', 0) or 0)}/"
            f"{int(card.get('total_units', 0) or 0)} unit"
        )
        source_text = str(card.get("source", "") or "")
        title_text = stage_label or f"Blok chat #{card.get('chunk', '')}"
        return f"""
            <section class="ner-block-card {quality_class}">
                <div class="ner-block-head">
                    <div>
                        <div class="block-title-row">
                            <span class="block-title">{escape(str(title_text))}</span>
                            <span class="block-type">Analitik per blok</span>
                        </div>
                        <div class="block-subtitle">Evaluasi memakai confidence kontekstual dari hasil tangkapan IndoBERT NER.</div>
                    </div>
                    <div class="block-pills">
                        {f"<span>{escape(batch_label)}</span>" if batch_label else ""}
                        <span>Conf {pct_text(avg_conf)}</span>
                        <span>Output {escape(str(card.get("rows_count", 0)))} baris</span>
                        <span class="order-status {status_class}">{escape(order_status)} {escape(unit_summary)}</span>
                        <span class="problem-status {'problem' if problem_count else 'ok'}">{'BERMASALAH ' + escape(str(problem_count)) if problem_count else 'OK'}</span>
                    </div>
                </div>
                <div class="ner-block-grid">
                    <div class="panel">
                        <div class="panel-title section-title">Chat asli per blok</div>
                        <pre class="chat-original">{escape(source_text)}</pre>
                    </div>
                    <div class="panel">
                        <div class="panel-title model-title">indolem/indobert-base-uncased</div>
                        {attr_table_html(card.get("attr_rows", []))}
                    </div>
                </div>
                <div class="panel output-panel">
                    <div class="panel-title section-title">Output Yang di Hasilkan Sistem</div>
                    {output_table_html(card.get("output_rows", []), card.get("red_output_columns", []), card.get("red_output_cells", []))}
                </div>
            </section>
            """

    def order_group_html(group: Dict[str, object]) -> str:
        group_cards = list(group.get("cards", []) or [])
        final_card = group_cards[-1] if group_cards else {}
        avg_values = [float(card.get("avg_confidence", 0.0) or 0.0) for card in group_cards]
        avg_conf = sum(avg_values) / len(avg_values) if avg_values else 0.0
        total_units = int(final_card.get("total_units", 0) or 0)
        complete_units = int(final_card.get("complete_units", 0) or 0)
        status = "LENGKAP" if total_units and complete_units == total_units else "BELUM LENGKAP"
        status_class = "complete" if status == "LENGKAP" else "incomplete"
        problem_count = sum(int(card.get("problem_count", card.get("needs_check", 0)) or 0) for card in group_cards)
        order_class = "good" if problem_count == 0 else "warn" if avg_conf >= 0.70 else "bad"

        stage_details = []
        for stage_idx, card in enumerate(group_cards, start=1):
            batch_label = str(card.get("batch_label", "") or "")
            stage_title = f"Tahap {stage_idx} - Blok chat #{card.get('chunk', '')}"
            stage_details.append(
                f"""
                <details class="ner-stage-detail"{' open' if stage_idx == len(group_cards) else ''}>
                    <summary>{escape(stage_title)}{f" <span>{escape(batch_label)}</span>" if batch_label else ""}</summary>
                    <div class="ner-block-grid ner-stage-grid">
                        <div class="panel">
                            <div class="panel-title section-title">Chat asli tahap {stage_idx}</div>
                            <pre class="chat-original">{escape(str(card.get("source", "") or ""))}</pre>
                        </div>
                        <div class="panel">
                            <div class="panel-title model-title">indolem/indobert-base-uncased</div>
                            {attr_table_html(card.get("attr_rows", []))}
                        </div>
                    </div>
                </details>
                """
            )

        return f"""
        <section class="ner-order-card {order_class}">
            <div class="ner-block-head">
                <div>
                    <div class="block-title-row">
                        <span class="block-title">Order gabungan NER #{escape(str(group.get('index', '')))}</span>
                        <span class="block-type">Gabungan hasil rekonsiliasi</span>
                    </div>
                    <div class="block-subtitle">{escape(str(group.get('summary', '') or 'Order gabungan'))}</div>
                </div>
                <div class="block-pills">
                    <span>{len(group_cards)} tahap chat</span>
                    <span>Conf rata-rata {pct_text(avg_conf)}</span>
                    <span class="order-status {status_class}">{status} {complete_units}/{total_units} unit</span>
                    <span class="problem-status {'problem' if problem_count else 'ok'}">{'BERMASALAH ' + escape(str(problem_count)) if problem_count else 'OK'}</span>
                </div>
            </div>
            <div class="ner-order-timeline">
                {''.join(stage_details)}
            </div>
            <div class="panel output-panel">
                <div class="panel-title section-title">Output akhir order gabungan</div>
                {output_table_html(final_card.get("output_rows", []), final_card.get("red_output_columns", []), final_card.get("red_output_cells", []))}
            </div>
        </section>
        """

    grouped_orders = list(grouped_orders or [])
    grouped_card_ids = {
        str(card_id)
        for group in grouped_orders
        for card_id in (group.get("card_ids", []) or [])
    }

    display_items: List[tuple[str, object]] = []
    for group in grouped_orders:
        display_items.append(("group", group))
    for card in cards:
        if ner_eval_card_identity(card) not in grouped_card_ids:
            display_items.append(("card", card))

    if max_items is not None:
        display_items = display_items[: max(0, int(max_items))]

    cards_html = []
    for item_type, item in display_items:
        if item_type == "group":
            cards_html.append(order_group_html(item))
        else:
            cards_html.append(block_stage_html(item))

    html = f"""
    <style>
    .simple-ner-eval {{
        height: {height}px;
        overflow: auto;
        border: 1px solid #d6dee8;
        border-radius: 8px;
        background: #eef2f7;
        padding: 14px;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .ner-block-card {{
        border: 1px solid #cbd5e1;
        border-left: 6px solid #16a34a;
        border-radius: 8px;
        background: #fff;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        overflow: hidden;
    }}
    .ner-order-card {{
        border: 1px solid #cbd5e1;
        border-left: 6px solid #0f9f6e;
        border-radius: 8px;
        background: #fff;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        overflow: hidden;
    }}
    .ner-order-card.warn {{ border-left-color: #d97706; }}
    .ner-order-card.bad {{ border-left-color: #dc2626; }}
    .ner-block-card.warn {{ border-left-color: #d97706; }}
    .ner-block-card.bad {{ border-left-color: #dc2626; }}
    .ner-block-card:last-child,
    .ner-order-card:last-child {{ margin-bottom: 0; }}
    .ner-block-head {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        padding: 12px 14px;
        border-bottom: 1px solid #d6dee8;
        background: #f8fafc;
    }}
    .ner-block-card.good .ner-block-head {{ background: #f0fdf4; }}
    .ner-block-card.warn .ner-block-head {{ background: #fffbeb; }}
    .ner-block-card.bad .ner-block-head {{ background: #fef2f2; }}
    .ner-order-card.good .ner-block-head {{ background: #ecfdf5; }}
    .ner-order-card.warn .ner-block-head {{ background: #fffbeb; }}
    .ner-order-card.bad .ner-block-head {{ background: #fef2f2; }}
    .block-title-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}
    .block-title {{
        font-size: 18px;
        font-weight: 800;
        color: #111827;
    }}
    .block-type {{
        border: 1px solid #cbd5e1;
        background: #ffffff;
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0;
    }}
    .block-subtitle {{
        margin-top: 4px;
        font-size: 11px;
        color: #475569;
    }}
    .block-pills {{
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        justify-content: flex-end;
    }}
    .block-pills span {{
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #fff;
        padding: 5px 8px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
    }}
    .block-pills span.order-status.complete {{
        background: #dcfce7;
        border-color: #86efac;
        color: #166534;
    }}
    .block-pills span.order-status.incomplete {{
        background: #fef3c7;
        border-color: #facc15;
        color: #854d0e;
    }}
    .block-pills span.problem-status.ok {{
        background: #dcfce7;
        border-color: #86efac;
        color: #166534;
    }}
    .block-pills span.problem-status.problem {{
        background: #fee2e2;
        border-color: #f87171;
        color: #991b1b;
    }}
    .ner-block-grid {{
        display: grid;
        grid-template-columns: minmax(330px, 0.85fr) minmax(560px, 1.45fr);
        gap: 12px;
        padding: 12px;
        align-items: start;
    }}
    .panel {{
        border: 1px solid #d6dee8;
        border-radius: 6px;
        background: #fff;
        min-width: 0;
        overflow: hidden;
    }}
    .panel-title {{
        display: flex;
        justify-content: space-between;
        gap: 8px;
        align-items: center;
        border-bottom: 1px solid #d6dee8;
        background: #f1f5f9;
        padding: 8px 10px;
        font-size: 12px;
        font-weight: 700;
        color: #111827;
    }}
    .panel-subtitle {{
        font-size: 10px;
        font-weight: 700;
        color: #64748b;
        white-space: nowrap;
    }}
    .panel-title.model-title {{
        justify-content: center;
        text-align: center;
        font-size: 15px;
        font-weight: 800;
    }}
    .panel-title.section-title {{
        font-size: 14px;
        font-weight: 800;
    }}
    .chat-original {{
        margin: 0;
        padding: 10px 12px;
        max-height: 320px;
        overflow: auto;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: Consolas, "Courier New", monospace;
        font-size: 11px;
        line-height: 1.45;
        background: #fbfefc;
        color: #111827;
    }}
    .mini-table-wrap {{
        max-height: 230px;
        overflow: auto;
        background: #fff;
    }}
    table.mini-excel {{
        border-collapse: collapse;
        table-layout: fixed;
        width: max-content;
        min-width: 100%;
        font-size: 10.5px;
        color: #000;
    }}
    table.mini-excel th {{
        position: sticky;
        top: 0;
        z-index: 2;
        border: 1px solid #334155;
        background: #e89393;
        padding: 5px 4px;
        text-align: center;
        font-weight: 700;
        white-space: nowrap;
    }}
    table.mini-excel td {{
        border: 1px solid #334155;
        padding: 4px 5px;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        background: #fff;
    }}
    table.mini-excel tr.partial-row td {{
        background: #fff3b0;
    }}
    table.mini-excel td.red-border-cell {{
        box-shadow: inset 0 0 0 2px #dc2626;
    }}
    .empty-output {{
        padding: 14px;
        font-size: 12px;
        color: #475569;
    }}
    .output-panel {{
        margin: 0 12px 12px 12px;
    }}
    .ner-order-timeline {{
        padding: 12px 12px 0 12px;
    }}
    .ner-stage-detail {{
        border: 1px solid #d6dee8;
        border-radius: 7px;
        background: #fff;
        margin-bottom: 10px;
        overflow: hidden;
    }}
    .ner-stage-detail summary {{
        cursor: pointer;
        padding: 9px 11px;
        background: #f8fafc;
        border-bottom: 1px solid #d6dee8;
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
    }}
    .ner-stage-detail summary span {{
        margin-left: 8px;
        border: 1px solid #cbd5e1;
        border-radius: 999px;
        padding: 2px 7px;
        font-size: 10px;
        color: #475569;
        background: #fff;
    }}
    .ner-stage-grid {{
        padding: 10px;
    }}
    table.attr-check {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        font-size: 11px;
    }}
    table.attr-check th {{
        border: 1px solid #334155;
        background: #f3f4f6;
        padding: 6px 5px;
        text-align: center;
        font-weight: 700;
    }}
    table.attr-check td {{
        border: 1px solid #334155;
        padding: 5px 6px;
        vertical-align: top;
        word-break: break-word;
        background: #fff;
    }}
    table.attr-check td.ner-values-cell {{
        padding: 0;
    }}
    .ner-single-value {{
        display: block;
        padding: 5px 6px;
        min-height: 17px;
    }}
    .ner-value-grid {{
        display: grid;
        width: 100%;
        min-height: 27px;
        background: transparent;
    }}
    .ner-value-grid span {{
        display: flex;
        align-items: center;
        min-height: 27px;
        padding: 5px 6px;
        border-right: 1px solid #334155;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .ner-value-grid span:last-child {{
        border-right: 0;
    }}
    .ner-single-value.red-border-value,
    .ner-value-grid span.red-border-value {{
        box-shadow: inset 0 0 0 2px #dc2626;
    }}
    table.attr-check th:nth-child(1), table.attr-check td:nth-child(1) {{ width: 120px; font-weight: 700; }}
    table.attr-check th:nth-child(3), table.attr-check td:nth-child(3) {{ width: 95px; text-align: center; font-weight: 700; }}
    table.attr-check tr.ok td {{ background: #fff; }}
    table.attr-check tr.warn td {{ background: #fff; }}
    table.attr-check tr.miss td {{ background: #fff; }}
    @media (max-width: 900px) {{
        .ner-block-head {{ align-items: flex-start; flex-direction: column; }}
        .block-pills {{ justify-content: flex-start; }}
        .ner-block-grid {{ grid-template-columns: 1fr; }}
    }}
    </style>
    <div class="simple-ner-eval">{''.join(cards_html)}</div>
    """
    st.html(html)


def render_ner_analytics_section(
    excel_df: pd.DataFrame,
    ner_audits: Sequence[Dict[str, object]],
    title: str = "Evaluasi NER per blok chat",
    key_prefix: str = "ner_eval",
    match_history: Sequence[Dict[str, object]] | None = None,
) -> None:
    st.subheader(title)
    simple_eval_cards = build_simple_ner_eval_cards(excel_df, ner_audits)
    if simple_eval_cards:
        def card_problematic(card: Dict[str, object]) -> bool:
            return int(card.get("problem_count", card.get("needs_check", 0)) or 0) > 0

        def card_batch_label(card: Dict[str, object]) -> str:
            batch_index = int(card.get("batch_index", 0) or 0)
            batch_label = str(card.get("batch_label", "") or "").strip()
            if batch_label:
                return batch_label
            return f"Batch {batch_index}" if batch_index else "Batch manual"

        batch_entries = []
        seen_batches = set()
        for card in simple_eval_cards:
            batch_index = int(card.get("batch_index", 0) or 0)
            batch_label = card_batch_label(card)
            batch_key = batch_index if batch_index else batch_label
            if batch_key in seen_batches:
                continue
            seen_batches.add(batch_key)
            batch_entries.append((batch_key, batch_label, batch_index))

        latest_batch_index = max(
            [int(card.get("batch_index", 0) or 0) for card in simple_eval_cards],
            default=0,
        )
        batch_options = ["Semua batch"]
        if latest_batch_index:
            batch_options.append("Batch terbaru")
        batch_options.extend(label for _, label, _ in batch_entries)

        available_groups = build_ner_stage2_card_groups(simple_eval_cards, match_history)
        view_options = ["Per blok chat"]
        if available_groups:
            view_options.insert(0, "Per order gabungan")

        filter_cols = st.columns([1.15, 1.15, 0.95, 1.05])
        selected_view = filter_cols[0].selectbox(
            "Mode tampilan",
            options=view_options,
            index=0,
            key=f"{key_prefix}_view_mode",
        )
        selected_batch = filter_cols[1].selectbox(
            "Batch ekstraksi",
            options=batch_options,
            index=0,
            key=f"{key_prefix}_batch_filter",
        )
        selected_status = filter_cols[2].selectbox(
            "Status pesanan",
            options=["Semua status", "Lengkap", "Belum lengkap"],
            index=0,
            key=f"{key_prefix}_status_filter",
        )
        condition_mode = filter_cols[3].selectbox(
            "Kondisi analitik",
            options=["Semua", "OK", "Bermasalah"],
            index=0,
            key=f"{key_prefix}_condition_filter",
        )

        filtered_cards = list(simple_eval_cards)
        if selected_batch == "Batch terbaru" and latest_batch_index:
            filtered_cards = [
                card
                for card in filtered_cards
                if int(card.get("batch_index", 0) or 0) == latest_batch_index
            ]
        elif selected_batch != "Semua batch":
            filtered_cards = [
                card
                for card in filtered_cards
                if card_batch_label(card) == selected_batch
            ]

        def card_matches_active_filters(card: Dict[str, object]) -> bool:
            if selected_status != "Semua status":
                expected_status = (
                    "LENGKAP" if selected_status == "Lengkap" else "BELUM LENGKAP"
                )
                if str(card.get("order_status", "") or "") != expected_status:
                    return False
            if condition_mode == "OK" and card_problematic(card):
                return False
            if condition_mode == "Bermasalah" and not card_problematic(card):
                return False
            return True

        grouped_orders: List[Dict[str, object]] = []
        if selected_view == "Per order gabungan":
            candidate_groups = build_ner_stage2_card_groups(filtered_cards, match_history)
            candidate_grouped_card_ids = {
                str(card_id)
                for group in candidate_groups
                for card_id in (group.get("card_ids", []) or [])
            }

            for group in candidate_groups:
                group_cards = [
                    card
                    for card in (group.get("cards", []) or [])
                    if isinstance(card, dict)
                ]
                if not group_cards:
                    continue
                final_card = group_cards[-1]
                if selected_status != "Semua status":
                    expected_status = (
                        "LENGKAP" if selected_status == "Lengkap" else "BELUM LENGKAP"
                    )
                    if str(final_card.get("order_status", "") or "") != expected_status:
                        continue
                group_problematic = any(card_problematic(card) for card in group_cards)
                if condition_mode == "OK" and group_problematic:
                    continue
                if condition_mode == "Bermasalah" and not group_problematic:
                    continue
                grouped_orders.append(group)

            selected_group_card_ids = {
                str(card_id)
                for group in grouped_orders
                for card_id in (group.get("card_ids", []) or [])
            }
            ungrouped_cards = [
                card
                for card in filtered_cards
                if ner_eval_card_identity(card) not in candidate_grouped_card_ids
                and card_matches_active_filters(card)
            ]
            ungrouped_card_ids = {
                ner_eval_card_identity(card) for card in ungrouped_cards
            }
            filtered_cards = [
                card
                for card in filtered_cards
                if ner_eval_card_identity(card) in selected_group_card_ids
                or ner_eval_card_identity(card) in ungrouped_card_ids
            ]
        else:
            filtered_cards = [
                card for card in filtered_cards if card_matches_active_filters(card)
            ]

        if not filtered_cards:
            st.info("Tidak ada blok chat yang cocok dengan filter analitik saat ini.")
            return

        grouped_card_ids = {
            str(card_id)
            for group in grouped_orders
            for card_id in (group.get("card_ids", []) or [])
        }
        display_count = len(grouped_orders) + sum(
            1 for card in filtered_cards if ner_eval_card_identity(card) not in grouped_card_ids
        )
        if display_count <= 1:
            eval_limit = 1
            st.caption("1 item analitik tersedia, evaluasi langsung ditampilkan.")
        else:
            eval_limit = st.slider(
                "Jumlah item yang ditampilkan",
                min_value=1,
                max_value=display_count,
                value=min(10, display_count),
                step=1,
                key=f"{key_prefix}_limit_{display_count}",
            )

        metric_groups = available_groups if selected_view == "Per order gabungan" else []
        metric_grouped_card_ids = {
            str(card_id)
            for group in metric_groups
            for card_id in (group.get("card_ids", []) or [])
        }
        metric_items: List[tuple[str, Dict[str, object]]] = [
            ("group", group) for group in metric_groups
        ]
        metric_items.extend(
            ("card", card)
            for card in simple_eval_cards
            if ner_eval_card_identity(card) not in metric_grouped_card_ids
        )

        def metric_item_cards(item_type: str, item: Dict[str, object]) -> List[Dict[str, object]]:
            if item_type == "group":
                return [
                    card
                    for card in (item.get("cards", []) or [])
                    if isinstance(card, dict)
                ]
            return [item]

        def metric_item_avg_confidence(item_type: str, item: Dict[str, object]) -> float:
            cards = metric_item_cards(item_type, item)
            values = [
                float(card.get("avg_confidence", 0.0) or 0.0)
                for card in cards
            ]
            return sum(values) / len(values) if values else 0.0

        def metric_item_complete(item_type: str, item: Dict[str, object]) -> bool:
            cards = metric_item_cards(item_type, item)
            if not cards:
                return False
            final_card = cards[-1]
            return str(final_card.get("order_status", "") or "") == "LENGKAP"

        def metric_item_problematic(item_type: str, item: Dict[str, object]) -> bool:
            return any(card_problematic(card) for card in metric_item_cards(item_type, item))

        avg_block_conf = (
            sum(metric_item_avg_confidence(item_type, item) for item_type, item in metric_items)
            / len(metric_items)
            if metric_items
            else 0.0
        )
        complete_orders = sum(
            1 for item_type, item in metric_items if metric_item_complete(item_type, item)
        )
        ok_blocks = sum(
            1 for item_type, item in metric_items if not metric_item_problematic(item_type, item)
        )
        problem_blocks = sum(
            1 for item_type, item in metric_items if metric_item_problematic(item_type, item)
        )
        eval_metrics = st.columns(5)
        eval_metrics[0].metric("Avg confidence NER", pct_text(avg_block_conf))
        eval_metrics[1].metric("Total Order", len(metric_items))
        eval_metrics[2].metric("Order Terpenuhi", complete_orders)
        eval_metrics[3].metric("Analitik OK", ok_blocks)
        eval_metrics[4].metric("Bermasalah", problem_blocks)
        if len(filtered_cards) != len(simple_eval_cards):
            st.caption(f"Filter aktif: menampilkan {len(filtered_cards)} dari {len(simple_eval_cards)} blok chat.")
        if selected_view == "Per order gabungan" and grouped_orders:
            st.caption(
                f"Mode gabungan aktif: {len(grouped_orders)} order hasil rekonsiliasi ditampilkan sebagai satu analitik per order."
            )
        render_simple_ner_block_evaluation(
            filtered_cards,
            height=760,
            grouped_orders=grouped_orders,
            max_items=int(eval_limit),
        )
    else:
        st.info("Belum ada hasil NER untuk dievaluasi.")


def render_ner_audit_html(audits: Sequence[Dict[str, object]], max_items: int = 8) -> None:
    cards = []
    for audit in audits[:max_items]:
        labels = audit.get("labels", {})
        rows = []
        if isinstance(labels, dict):
            for label, values in labels.items():
                value_text = ", ".join(str(v) for v in values)
                rows.append(
                    f"<tr><td>{escape(str(label))}</td><td>{escape(value_text)}</td></tr>"
                )
        cards.append(
            f"""
            <div class="audit-card">
                <div class="audit-title">Chunk {escape(str(audit.get("chunk", "")))} | UNIT_QTY {escape(str(audit.get("qty_ner", "")))}</div>
                <pre>{escape(str(audit.get("ner_input", ""))[:700])}</pre>
                <table><tbody>{''.join(rows)}</tbody></table>
            </div>
            """
        )

    html = f"""
    <style>
    .audit-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        font-family: Arial, Helvetica, sans-serif;
    }}
    .audit-card {{
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }}
    .audit-title {{
        padding: 8px 10px;
        background: #f1f5f9;
        font-weight: 700;
        font-size: 12px;
    }}
    .audit-card table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }}
    .audit-card pre {{
        margin: 0;
        padding: 8px 10px;
        max-height: 130px;
        overflow: auto;
        white-space: pre-wrap;
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
        font-family: Consolas, "Courier New", monospace;
        font-size: 11px;
        color: #1f2937;
    }}
    .audit-card td {{
        border-top: 1px solid #e2e8f0;
        padding: 6px 8px;
        vertical-align: top;
    }}
    .audit-card td:first-child {{
        width: 110px;
        font-weight: 700;
        color: #334155;
    }}
    </style>
    <div class="audit-grid">{''.join(cards)}</div>
    """
    st.html(html)


def css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1600px; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stMetricValue"] { font-size: 1.45rem; }
        div[data-testid="stButton"] button {
            min-height: 38px;
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
            white-space: nowrap;
        }
        .dev-mode-link {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            position: fixed;
            top: 76px;
            right: 32px;
            z-index: 9999;
        }
        .dev-mode-link a {
            color: #334155;
            font-size: 0.72rem;
            font-weight: 600;
            line-height: 1;
            text-decoration: none;
        }
        .dev-mode-link a:hover {
            color: #0f172a;
            text-decoration: underline;
        }
        .st-key-hidden_dev_summary,
        .st-key-hidden_dev_suite,
        .st-key-hidden_dev_dataset {
            display: none !important;
        }
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            min-height: 38px;
        }
        .status-line {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 10px 12px;
            background: #f8fafc;
            margin: 6px 0 14px 0;
        }
        .risk-critical { color: #991b1b; font-weight: 700; }
        .risk-high { color: #9a3412; font-weight: 700; }
        .risk-medium { color: #075985; font-weight: 700; }
        .small-note { color: #475569; font-size: 0.88rem; }
        textarea { font-family: Consolas, "Courier New", monospace !important; font-size: 0.82rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Stage 2 IndoBERT Pair Test",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css()

    model_dirs = discover_model_dirs()
    default_index = 0
    if str(DEFAULT_MODEL_PATH) in model_dirs:
        default_index = model_dirs.index(str(DEFAULT_MODEL_PATH))

    with st.sidebar:
        st.subheader("Model")
        selected_model = st.selectbox("Folder model", model_dirs, index=default_index)
        model_path = st.text_input("Path aktif", selected_model)
        threshold = st.slider("Threshold MATCH", 0.05, 0.95, 0.50, 0.01)
        max_seq_len = st.selectbox("Max sequence length", [128, 256, 384, 512], index=1)
        batch_size = st.selectbox("Batch size inference", [1, 2, 4, 8, 16], index=3)
        require_gpu = st.toggle("Wajib GPU", value=True)

    tokenizer, model, device = load_model(model_path)
    if require_gpu and device.type != "cuda":
        st.error("CUDA tidak aktif. App dihentikan karena opsi Wajib GPU menyala.")
        st.stop()

    dev_param = str(st.query_params.get("dev", "0") or "0").strip().lower()
    dev_mode = dev_param in {"1", "true", "on"}
    next_dev_param = "0" if dev_mode else "1"
    dev_label = "dev: on" if dev_mode else "dev: off"
    dev_control_cols = st.columns([12, 1])
    with dev_control_cols[1]:
        st.markdown(
            f'<div class="dev-mode-link"><a href="?dev={next_dev_param}" '
            f'target="_self">{dev_label}</a></div>',
            unsafe_allow_html=True,
        )

    cases = build_operational_cases()
    pairs = [(item.text_a, item.text_b) for item in cases]
    predictions = predict_pairs(tokenizer, model, device, pairs, max_seq_len, threshold, batch_size)
    df = cases_to_dataframe(cases, predictions)
    metrics = metric_bundle(df)

    if dev_mode:
        (
            tab_summary,
            tab_suite,
            tab_custom,
            tab_ner_new_order,
            tab_model_eval,
            tab_dataset,
            tab_model,
        ) = st.tabs(
            [
                "Ringkasan",
                "Operational Suite",
                "Live Test",
                "Ekstraksi dan Rekonsiliasi",
                "Evaluasi Performa Model",
                "Dataset Sampler",
                "Model Info",
            ]
        )
    else:
        (
            tab_custom,
            tab_ner_new_order,
            tab_model_eval,
            tab_model,
        ) = st.tabs(
            [
                "Live Test",
                "Ekstraksi dan Rekonsiliasi",
                "Evaluasi Performa Model",
                "Model Info",
            ]
        )
        tab_summary = st.container(key="hidden_dev_summary")
        tab_suite = st.container(key="hidden_dev_suite")
        tab_dataset = st.container(key="hidden_dev_dataset")

    with tab_summary:
        render_metric_cards(metrics)

        left, right = st.columns([1.1, 0.9])
        with left:
            summary = (
                df.groupby("group", as_index=False)
                .agg(
                    total=("case_id", "count"),
                    passed=("status", lambda s: int((s == "PASS").sum())),
                    false_match=("error_type", lambda s: int((s == "FALSE_MATCH").sum())),
                    false_no_match=("error_type", lambda s: int((s == "FALSE_NO_MATCH").sum())),
                    avg_p_match=("p_match", "mean"),
                )
                .assign(pass_rate=lambda x: x["passed"] / x["total"])
            )
            st.subheader("Coverage per kelompok")
            st.dataframe(
                style_results(summary),
                width="stretch",
                hide_index=True,
                column_config={
                    "pass_rate": st.column_config.ProgressColumn(
                        "pass_rate",
                        min_value=0,
                        max_value=1,
                        format="%.1f%%",
                    )
                },
            )

        with right:
            st.subheader("Critical failure board")
            critical = df[(df["status"] == "FAIL") | (df["error_type"] == "FALSE_MATCH")]
            columns = [
                "case_id",
                "expected",
                "predicted",
                "error_type",
                "severity",
                "p_match",
                "gate",
                "focus",
                "rule_advisory",
            ]
            if critical.empty:
                st.success("Tidak ada failure pada suite bawaan.")
            else:
                st.dataframe(
                    style_results(critical[columns]),
                    width="stretch",
                    hide_index=True,
                )

        st.subheader("Matrix suite")
        matrix_cols = [
            "case_id",
            "group",
            "expected",
            "predicted",
            "status",
            "error_type",
            "severity",
            "p_match",
            "p_no_match",
            "gate",
            "rule_advisory",
            "focus",
        ]
        st.dataframe(
            style_results(df[matrix_cols]),
            width="stretch",
            hide_index=True,
        )

    with tab_suite:
        filters = st.columns(4)
        group_options = ["ALL"] + sorted(df["group"].unique().tolist())
        selected_group = filters[0].selectbox("Group", group_options)
        selected_expected = filters[1].selectbox("Expected", ["ALL", LABEL_MATCH, LABEL_NO_MATCH])
        selected_status = filters[2].selectbox("Status", ["ALL", "PASS", "FAIL"])
        only_false_match = filters[3].toggle("False MATCH only", value=False)

        view = df.copy()
        if selected_group != "ALL":
            view = view[view["group"] == selected_group]
        if selected_expected != "ALL":
            view = view[view["expected"] == selected_expected]
        if selected_status != "ALL":
            view = view[view["status"] == selected_status]
        if only_false_match:
            view = view[view["error_type"] == "FALSE_MATCH"]

        table_cols = [
            "case_id",
            "group",
            "expected",
            "predicted",
            "status",
            "error_type",
            "p_match",
            "confidence",
            "gate",
            "focus",
            "rule_advisory",
        ]
        st.dataframe(style_results(view[table_cols]), width="stretch", hide_index=True)

        for _, row in view.iterrows():
            title = (
                f"{row['case_id']} | {row['status']} | "
                f"{row['expected']} -> {row['predicted']} | P_MATCH {row['p_match']:.3f} | {row['focus']}"
            )
            with st.expander(title, expanded=row["status"] == "FAIL"):
                render_case_detail(row)

    with tab_custom:
        st.subheader("Live test per case")

        if "live_text_a" not in st.session_state:
            st.session_state.live_text_a = cases[0].text_a
        if "live_text_b" not in st.session_state:
            st.session_state.live_text_b = cases[0].text_b
        if "live_expected" not in st.session_state:
            st.session_state.live_expected = cases[0].expected

        case_options = {
            "Manual input": None,
            **{
                f"{item.case_id} | {item.expected} | {item.focus}": item
                for item in cases
            },
        }
        load_cols = st.columns([2.5, 1, 1, 1])
        selected_template = load_cols[0].selectbox(
            "Template case", list(case_options.keys()), key="live_template_case"
        )
        if load_cols[1].button("Load case", width="stretch"):
            selected_case = case_options[selected_template]
            if selected_case is not None:
                st.session_state.live_text_a = selected_case.text_a
                st.session_state.live_text_b = selected_case.text_b
                st.session_state.live_expected = selected_case.expected
        if load_cols[2].button("Clear", width="stretch"):
            st.session_state.live_text_a = ""
            st.session_state.live_text_b = ""
            st.session_state.live_expected = LABEL_MATCH
        run_live = load_cols[3].button("Run test", type="primary", width="stretch")

        c_left, c_right = st.columns(2)
        text_a = c_left.text_area(
            "Pesanan awal / order state",
            height=390,
            key="live_text_a",
        )
        text_b = c_right.text_area(
            "Pesanan susulan / incoming",
            height=390,
            key="live_text_b",
        )

        expected_cols = st.columns([1, 1, 2])
        expected_mode = expected_cols[0].radio(
            "Expected source",
            ["Manual", "Auto rule"],
            horizontal=True,
            key="live_expected_mode",
        )
        manual_expected = expected_cols[1].selectbox(
            "Expected manual",
            [LABEL_MATCH, LABEL_NO_MATCH],
            index=[LABEL_MATCH, LABEL_NO_MATCH].index(st.session_state.live_expected),
            key="live_expected",
        )

        pred = predict_pairs(
            tokenizer,
            model,
            device,
            [(clean_text(text_a), clean_text(text_b))],
            max_seq_len,
            threshold,
            batch_size=1,
        )[0]
        checks = operational_checks(text_a, text_b)
        auto_expected = expected_from_operational_checks(checks)
        expected = auto_expected if expected_mode == "Auto rule" else manual_expected
        rule_blocks_match = "BLOCK:" in str(checks.get("rule_advisory", "") or "")
        active_predicted = LABEL_NO_MATCH if rule_blocks_match else str(pred["predicted"])
        status, error_type, assessment = result_status(expected, active_predicted)
        if rule_blocks_match and str(pred["predicted"]) == LABEL_MATCH:
            assessment = (
                "Rule tanggal memblokir MATCH model karena konteks wajib berbeda. "
                + assessment
            )

        expected_cols[2].dataframe(
            pd.DataFrame(
                [
                    {
                        "expected_manual": manual_expected,
                        "expected_auto_rule": auto_expected,
                        "expected_active": expected,
                    }
                ]
            ),
            width="stretch",
            hide_index=True,
        )

        cols = st.columns(6)
        cols[0].metric("Expected", expected)
        cols[1].metric("Predicted", active_predicted)
        cols[2].metric("Status", status)
        cols[3].metric("P_MATCH", f"{float(pred['p_match']):.3f}")
        cols[4].metric("P_NO_MATCH", f"{float(pred['p_no_match']):.3f}")
        cols[5].metric("Confidence", f"{float(pred['confidence']):.3f}")

        live_row = pd.DataFrame(
            [
                {
                    "expected": expected,
                    "predicted": active_predicted,
                    "model_predicted": pred["predicted"],
                    "status": status,
                    "error_type": error_type,
                    "p_match": float(pred["p_match"]),
                    "p_no_match": float(pred["p_no_match"]),
                    "confidence": float(pred["confidence"]),
                    "threshold": threshold,
                    "max_seq_len": max_seq_len,
                    "assessment": assessment,
                    "rule_advisory": checks["rule_advisory"],
                }
            ]
        )
        st.dataframe(style_results(live_row), width="stretch", hide_index=True)

        if checks["rule_advisory"] == "OK":
            st.success("Rule advisory: OK")
        else:
            st.warning(f"Rule advisory: {checks['rule_advisory']}")

        if status == "PASS":
            st.success(assessment)
        elif error_type == "FALSE_MATCH":
            st.error(assessment)
        else:
            st.warning(assessment)

        st.dataframe(pd.DataFrame([checks]), width="stretch", hide_index=True)

    with tab_ner_new_order:
       

        db_ready = init_operational_db_once()
        if "ner_new_order_text" not in st.session_state:
            st.session_state.ner_new_order_text = ""
        if "ner_db_status_message" not in st.session_state:
            st.session_state.ner_db_status_message = ""

        ner_model_path = str(DEFAULT_NER_MODEL_PATH)
        ner_max_seq_len = 256
        excel_height = 620

        def reset_db_output() -> None:
            if not db_ready or db_reset_all_data is None:
                st.session_state.ner_db_status_message = "Database belum aktif. Cek konfigurasi `.env` / PostgreSQL."
                return
            try:
                reset_info = db_reset_all_data()
                st.session_state.ner_new_order_text = ""
                st.session_state.ner_saved_db_df = pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])
                st.session_state.ner_last_auto_db_signature = ""
                st.session_state.ner_db_status_message = (
                    "DB dan output berhasil direset "
                    f"(order_dataset: {reset_info.get('order_dataset_deleted', 0)}, "
                    f"raw_chats: {reset_info.get('raw_chats_deleted', 0)}, "
                    f"stage2_audit: {reset_info.get('stage2_match_audits_deleted', 0)})."
                )
            except Exception as e:
                st.session_state.ner_db_status_message = f"Gagal reset DB/output: {e}"
            st.session_state.ner_normalized_output = False

        def enable_normalized_output() -> None:
            st.session_state.ner_normalized_output = bool(OPERATIONAL_NORMALIZATION_ENABLED)

        def disable_normalized_output() -> None:
            st.session_state.ner_normalized_output = False

        def render_output_buttons(key_prefix: str) -> bool:
            if OPERATIONAL_NORMALIZATION_ENABLED:
                output_cols = st.columns([0.95, 0.72, 0.9, 0.9, 4.45])
                output_cols[0].button(
                    "Normalisasi",
                    type="primary",
                    width="stretch",
                    key=f"{key_prefix}_normalize",
                    on_click=enable_normalized_output,
                )
                output_cols[1].button(
                    "Reset Raw",
                    width="stretch",
                    key=f"{key_prefix}_reset_raw",
                    on_click=disable_normalized_output,
                )
                reset_col = output_cols[2]
                filter_col = output_cols[3]
            else:
                output_cols = st.columns([0.9, 0.9, 5.95])
                reset_col = output_cols[0]
                filter_col = output_cols[1]

            reset_clicked = reset_col.button(
                "Reset Output",
                width="stretch",
                key=f"{key_prefix}_reset_db_output",
                on_click=reset_db_output,
            )
            filter_col.selectbox(
                "Status",
                ["Semua", "Lengkap", "Belum lengkap"],
                index=0,
                key=f"{key_prefix}_completion_filter",
                label_visibility="collapsed",
            )
            return bool(reset_clicked)

        raw_new_order_text = st.text_area(
            "Input chat pesanan baru harian",
            height=310,
            key="ner_new_order_text",
        )
        if not OPERATIONAL_NORMALIZATION_ENABLED:
            st.session_state.ner_normalized_output = False
        input_action_cols = st.columns([4.5, 1.0])
        run_ner_now = input_action_cols[1].button(
            "Mulai Ekstraksi",
            type="primary",
            width="stretch",
            key="ner_start_extraction",
        )

        should_run_ner = bool(raw_new_order_text.strip())
        if not should_run_ner:
            saved_df = load_db_excel_df() if db_ready else pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])
            status_message = str(st.session_state.get("ner_db_status_message", "") or "")
            if status_message:
                st.info(status_message)

            output_source_df = saved_df
            if not output_source_df.empty:
                display_saved_df_full = (
                    normalize_operational_excel(output_source_df)
                    if OPERATIONAL_NORMALIZATION_ENABLED
                    and st.session_state.get("ner_normalized_output", False)
                    and not output_source_df.empty
                    else output_source_df
                )
                render_output_summary_metrics(display_saved_df_full)
                render_output_buttons("ner_idle_output")
                display_saved_df_view = filter_output_by_completion(
                    display_saved_df_full,
                    st.session_state.get("ner_idle_output_completion_filter", "Semua"),
                )
                render_excel_like_table(display_saved_df_view, height=int(excel_height))
            else:
                st.info("Paste chat pesanan baru, lalu mulai ekstraksi. Output DB masih kosong.")
        else:
            ner_tokenizer, ner_model, ner_device = load_ner_model(ner_model_path)
            if require_gpu and ner_device.type != "cuda":
                st.error("CUDA tidak aktif untuk NER. App dihentikan karena opsi Wajib GPU menyala.")
                st.stop()

            excel_df, ner_audits = rows_from_new_order_text(
                ner_tokenizer,
                ner_model,
                ner_device,
                raw_new_order_text,
                int(ner_max_seq_len),
            )
            result_signature = (
                f"{len(raw_new_order_text)}|{raw_new_order_text[:120]}|"
                f"{raw_new_order_text[-120:]}|{ner_model_path}|{ner_max_seq_len}"
            )
            if st.session_state.get("ner_result_signature") != result_signature:
                st.session_state.ner_result_signature = result_signature
                st.session_state.ner_normalized_output = False

            if excel_df.empty:
                st.warning("Tidak ada baris hasil ekstraksi NER.")
            else:
                input_chunks = split_new_order_messages(raw_new_order_text)
                use_intra_batch_sync = bool(db_ready and len(input_chunks) > 1)
                existing_df_before_sync = (
                    load_db_excel_df()
                    if db_ready
                    else pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])
                )
                stage2_preview_rows: List[Dict[str, object]] = []
                if db_ready and not use_intra_batch_sync and not existing_df_before_sync.empty:
                    with st.spinner("Mengecek kandidat pelengkapan dengan matcher tahap 2..."):
                        stage2_preview_rows = build_stage2_match_preview(
                            existing_df_before_sync,
                            raw_new_order_text,
                            excel_df,
                            tokenizer,
                            model,
                            device,
                            max_seq_len=int(max_seq_len),
                            threshold=float(threshold),
                            batch_size=int(batch_size),
                        )

                auto_db_signature = result_signature
                if db_ready:
                    if st.session_state.get("ner_last_auto_db_signature") != auto_db_signature:
                        if use_intra_batch_sync:
                            with st.spinner("Memproses multi-blok secara berurutan untuk pencocokan intra-batch..."):
                                db_display_df, db_message, stage2_preview_rows = sync_extraction_blocks_sequentially(
                                    raw_new_order_text,
                                    ner_tokenizer,
                                    ner_model,
                                    ner_device,
                                    int(ner_max_seq_len),
                                    tokenizer,
                                    model,
                                    device,
                                    int(max_seq_len),
                                    float(threshold),
                                    int(batch_size),
                                )
                        else:
                            stage2_apply_row = stage2_preview_rows[0] if stage2_preview_rows else None
                            db_display_df, db_message = sync_extraction_to_db(
                                raw_new_order_text,
                                excel_df,
                                stage2_apply_row,
                            )
                        st.session_state.ner_last_auto_db_signature = auto_db_signature
                        st.session_state.ner_saved_db_df = db_display_df
                        st.session_state.ner_db_status_message = db_message
                        if stage2_preview_rows and not use_intra_batch_sync:
                            audit_signature = (
                                f"{auto_db_signature}|"
                                f"{stage2_preview_rows[0].get('candidate_key', '')}|"
                                f"{stage2_preview_rows[0].get('p_match', 0.0)}"
                            )
                            if st.session_state.get("stage2_match_audit_signature") != audit_signature:
                                try:
                                    save_stage2_match_preview(raw_new_order_text, stage2_preview_rows)
                                    st.session_state.stage2_match_audit_signature = audit_signature
                                except Exception:
                                    pass
                    else:
                        db_display_df = load_db_excel_df()
                        st.session_state.ner_saved_db_df = db_display_df
                        db_message = str(st.session_state.get("ner_db_status_message", "") or "")
                        if use_intra_batch_sync:
                            stage2_preview_rows = latest_stage2_match_group()
                else:
                    db_display_df = pd.DataFrame(columns=EXCEL_COLUMNS + ["status_unit"])
                    db_message = "Database belum aktif. Output sementara hanya dari batch NER saat ini."

                table_source_df = (
                    db_display_df
                    if isinstance(db_display_df, pd.DataFrame) and not db_display_df.empty
                    else excel_df
                )
                raw_chats = load_all_raw_chat_records_from_db() if db_ready else []
                cumulative_audits: List[Dict[str, object]] = []
                if raw_chats:
                    with st.spinner("Membangun output dan analitik kumulatif dari semua batch DB..."):
                        cumulative_df, cumulative_audits = cumulative_rows_and_audits_from_raw_chats(
                            ner_tokenizer,
                            ner_model,
                            ner_device,
                            raw_chats,
                            int(ner_max_seq_len),
                            bool(
                                OPERATIONAL_NORMALIZATION_ENABLED
                                and st.session_state.get("ner_normalized_output", False)
                            ),
                        )

                table_df = (
                    normalize_operational_excel(table_source_df)
                    if OPERATIONAL_NORMALIZATION_ENABLED
                    and st.session_state.get("ner_normalized_output", False)
                    and not table_source_df.empty
                    else table_source_df
                )
                render_output_summary_metrics(table_df)
                render_output_buttons("ner_live_output")
                table_view_df = filter_output_by_completion(
                    table_df,
                    st.session_state.get("ner_live_output_completion_filter", "Semua"),
                )
                render_excel_like_table(table_view_df, height=int(excel_height))
                st.session_state.ner_latest_eval_df = table_df
                st.session_state.ner_latest_eval_audits = ner_audits
                if stage2_preview_rows:
                    st.session_state.stage2_latest_preview_rows = stage2_preview_rows

                csv_source_df = table_df if isinstance(table_df, pd.DataFrame) and not table_df.empty else excel_df
                csv = csv_source_df[EXCEL_COLUMNS].to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV output DB realtime",
                    data=csv,
                    file_name="ner_pesanan_baru_db_realtime.csv",
                    mime="text/csv",
                )

    with tab_model_eval:
        st.subheader("Evaluasi Performa Model")
        ner_eval_tab, matcher_eval_tab = st.tabs(["Analitik Ekstraksi", "Analitik Rekonsiliasi"])

        with ner_eval_tab:
            raw_chats = load_all_raw_chat_records_from_db() if db_ready else []
            if raw_chats:
                ner_tokenizer, ner_model, ner_device = load_ner_model(ner_model_path)
                if require_gpu and ner_device.type != "cuda":
                    st.error("CUDA tidak aktif untuk NER. Evaluasi NER tidak dapat dijalankan saat opsi Wajib GPU menyala.")
                else:
                    match_history_for_ner = load_stage2_match_history(500) if db_ready else []
                    with st.spinner("Membangun analitik NER dari seluruh batch DB..."):
                        cumulative_df, cumulative_audits = cumulative_rows_and_audits_from_raw_chats(
                            ner_tokenizer,
                            ner_model,
                            ner_device,
                            raw_chats,
                            int(ner_max_seq_len),
                            bool(
                                OPERATIONAL_NORMALIZATION_ENABLED
                                and st.session_state.get("ner_normalized_output", False)
                            ),
                        )
                    analytics_source_df = (
                        cumulative_df
                        if isinstance(cumulative_df, pd.DataFrame) and not cumulative_df.empty
                        else load_db_excel_df()
                    )
                    render_ner_analytics_section(
                        analytics_source_df,
                        cumulative_audits,
                        title="Evaluasi NER",
                        key_prefix="model_eval_ner",
                        match_history=match_history_for_ner,
                    )
            else:
                fallback_df = st.session_state.get("ner_latest_eval_df", pd.DataFrame())
                fallback_audits = st.session_state.get("ner_latest_eval_audits", [])
                if isinstance(fallback_df, pd.DataFrame) and not fallback_df.empty and fallback_audits:
                    render_ner_analytics_section(
                        fallback_df,
                        fallback_audits,
                        title="Evaluasi NER per blok chat terakhir",
                        key_prefix="model_eval_ner_fallback",
                        match_history=load_stage2_match_history(500) if db_ready else [],
                    )
                else:
                    st.info("Belum ada raw chat tersimpan untuk evaluasi NER. Jalankan ekstraksi terlebih dahulu.")

        with matcher_eval_tab:
            match_history = load_stage2_match_history(500) if db_ready else []
            latest_match_rows = list(st.session_state.get("stage2_latest_preview_rows", []) or [])

            if match_history:
                top_events = stage2_top_events_from_history(match_history)
                filter_cols = st.columns([1.0, 1.15, 0.85, 2.3])
                audit_scope = filter_cols[0].selectbox(
                    "Kategori audit",
                    ["Aman", "Conflict"],
                    index=0,
                    key="stage2_eval_scope_filter",
                )
                selected_events = (
                    [
                        event
                        for event in top_events
                        if stage2_is_anomaly_event(event)
                    ]
                    if audit_scope == "Conflict"
                    else [
                        event
                        for event in top_events
                        if stage2_is_confident_match_merge(event)
                    ]
                )
                timeline_filter = filter_cols[1].selectbox(
                    "Riwayat order",
                    ["Semua", "Bertahap", "Satu tahap"],
                    key="stage2_eval_timeline_filter",
                )
                max_orders = filter_cols[2].selectbox(
                    "Jumlah order",
                    [5, 10, 20, 50],
                    index=1,
                    key="stage2_eval_order_limit",
                )

                timeline_groups = stage2_order_timeline_groups_from_events(selected_events)
                timeline_groups = filter_stage2_timeline_groups(
                    timeline_groups,
                    str(timeline_filter),
                )
                total_groups = len(stage2_order_timeline_groups_from_events(selected_events))
                if audit_scope == "Conflict":
                    st.caption(
                        f"Filter aktif: menampilkan {min(len(timeline_groups), int(max_orders))} "
                        f"dari {total_groups} order conflict. "
                        "Conflict berisi kasus model ragu atau MATCH tidak aman; NO_MATCH yang jelas order baru tidak ditampilkan."
                    )
                else:
                    st.caption(
                        f"Filter aktif: menampilkan {min(len(timeline_groups), int(max_orders))} "
                        f"dari {total_groups} order MATCH siap gabung. "
                        "Default aman hanya menampilkan kasus model yakin MATCH dan sistem berhasil gabung."
                    )
                render_stage2_match_order_timeline(
                    groups=timeline_groups,
                    title=(
                        "Evaluasi conflict pencocokan order"
                        if audit_scope == "Conflict"
                        else "Evaluasi pencocokan order"
                    ),
                    subtitle=(
                        "Conflict berisi pasangan yang perlu audit karena skor model ragu atau MATCH tidak aman diterapkan."
                        if audit_scope == "Conflict"
                        else "Setiap blok mewakili satu order kandidat. Di dalamnya ditampilkan "
                        "riwayat tahap pencocokan saat chat susulan masuk bertahap."
                    ),
                    height=780,
                    max_orders=int(max_orders),
                )
            elif latest_match_rows:
                latest_top_events = stage2_top_events_from_history(latest_match_rows)
                latest_top = latest_top_events[0] if latest_top_events else latest_match_rows[0]
                fallback_scope = st.selectbox(
                    "Kategori audit",
                    ["Aman", "Conflict"],
                    index=0,
                    key="stage2_eval_scope_filter_fallback",
                )
                if fallback_scope == "Conflict":
                    fallback_events = [
                        event for event in latest_top_events if stage2_is_anomaly_event(event)
                    ]
                    if fallback_events:
                        render_stage2_match_order_timeline(
                            groups=stage2_order_timeline_groups_from_events(fallback_events),
                            title="Evaluasi conflict pencocokan order terakhir",
                            subtitle=(
                                "Conflict berisi pasangan yang perlu audit karena skor model ragu "
                                "atau MATCH tidak aman diterapkan."
                            ),
                            height=780,
                            max_orders=10,
                        )
                    else:
                        st.info("Hasil pencocokan terakhir tidak termasuk conflict.")
                elif stage2_is_confident_match_merge(latest_top):
                    render_stage2_match_card(
                        latest_match_rows,
                        title="Evaluasi pencocokan order",
                        subtitle=(
                            "Menyandingkan chat pesanan awal dan pesanan susulan, lalu menampilkan "
                            "probabilitas model serta dampak pengisian slot order."
                        ),
                        height=780,
                    )
                else:
                    st.info("Hasil pencocokan terakhir belum termasuk kategori aman. Pilih Conflict untuk melihat jika termasuk anomali.")
            else:
                st.info(
                    "Belum ada audit MATCH siap gabung. Jalankan pesanan susulan yang cocok "
                    "dengan order belum lengkap."
                )

    with tab_dataset:
        st.subheader("Sampler dataset training")
        dataset_path = st.text_input("Dataset path", str(DEFAULT_DATASET_PATH))
        dataset_df = load_training_dataset(dataset_path)
        if dataset_df.empty:
            st.warning("Dataset tidak ditemukan atau kosong.")
        else:
            kind_options = ["ALL"] + sorted(dataset_df.get("pair_kind", pd.Series(dtype=str)).dropna().unique().tolist())
            source_options = ["ALL"] + sorted(dataset_df.get("source_id", pd.Series(dtype=str)).dropna().unique().tolist())
            dcols = st.columns(5)
            selected_kind = dcols[0].selectbox("pair_kind", kind_options)
            selected_source = dcols[1].selectbox("source_id", source_options)
            selected_label = dcols[2].selectbox("label", ["ALL", LABEL_MATCH, LABEL_NO_MATCH])
            sample_n = dcols[3].slider("Sample", 10, 300, 50, 10)
            seed = dcols[4].number_input("Seed", min_value=1, max_value=9999, value=42, step=1)

            sample_df = dataset_df.copy()
            if selected_kind != "ALL" and "pair_kind" in sample_df:
                sample_df = sample_df[sample_df["pair_kind"] == selected_kind]
            if selected_source != "ALL" and "source_id" in sample_df:
                sample_df = sample_df[sample_df["source_id"] == selected_source]
            if selected_label != "ALL" and "label" in sample_df:
                sample_df = sample_df[sample_df["label"] == selected_label]

            sample_df = sample_df.sample(
                n=min(sample_n, len(sample_df)),
                random_state=int(seed),
            ) if not sample_df.empty else sample_df

            if sample_df.empty:
                st.warning("Filter dataset tidak menghasilkan baris.")
            else:
                ds_pairs = list(zip(sample_df["text_a"].astype(str), sample_df["text_b"].astype(str)))
                ds_pred = predict_pairs(
                    tokenizer,
                    model,
                    device,
                    ds_pairs,
                    max_seq_len,
                    threshold,
                    batch_size,
                )
                result = sample_df[
                    [
                        col
                        for col in [
                            "pair_id",
                            "label",
                            "pair_kind",
                            "unit_action",
                            "source_id",
                            "text_a",
                            "text_b",
                        ]
                        if col in sample_df.columns
                    ]
                ].copy()
                result["predicted"] = [p["predicted"] for p in ds_pred]
                result["p_match"] = [float(p["p_match"]) for p in ds_pred]
                result["confidence"] = [float(p["confidence"]) for p in ds_pred]
                result["status"] = [
                    "PASS" if expected == predicted else "FAIL"
                    for expected, predicted in zip(result["label"], result["predicted"])
                ]
                ds_metrics = metric_bundle(
                    result.rename(columns={"label": "expected"})[
                        ["expected", "predicted", "status"]
                    ].assign(
                        error_type=lambda x: [
                            "FALSE_MATCH"
                            if e == LABEL_NO_MATCH and p == LABEL_MATCH
                            else "FALSE_NO_MATCH"
                            if e == LABEL_MATCH and p == LABEL_NO_MATCH
                            else "-"
                            for e, p in zip(x["expected"], x["predicted"])
                        ]
                    )
                )
                render_metric_cards(ds_metrics)
                st.dataframe(
                    style_results(
                        result[
                            [
                                col
                                for col in [
                                    "pair_id",
                                    "label",
                                    "predicted",
                                    "status",
                                    "p_match",
                                    "confidence",
                                    "pair_kind",
                                    "unit_action",
                                    "source_id",
                                ]
                                if col in result.columns
                            ]
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )
                csv = result.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download hasil sampler CSV",
                    data=csv,
                    file_name="stage2_pair_dataset_sampler_result.csv",
                    mime="text/csv",
                )

    with tab_model:
        render_model_info_tab()


if __name__ == "__main__":
    main()
