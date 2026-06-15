import unittest
from unittest.mock import patch
import pandas as pd

from app import (
    apply_revision_to_existing_office_df,
    apply_revisions_from_chat,
    enforce_block_quota,
    extract_ro_date_from_text,
    mark_order_block,
)


class RevisionHandlingTests(unittest.TestCase):
    def test_revision_row_is_not_converted_to_new_order_row(self):
        df_raw = pd.DataFrame([
            {
                "UNIT_QTY": "3",
                "UNIT_TYPE": "TWB",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, PKU",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "TIME": "",
                "DATE": "17/2/2026",
                "Original_Text": "3 UNIT TWB\nLokasi : ARGOPANTES\nRute/tujuan : CGK - PKU",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "TWB",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, PKU",
                "DRIVER": "M Syaichoni",
                "PLATE": "N 8872 RK",
                "PHONE": "081231895971",
                "TIME": "18:00",
                "DATE": "17/2/2026",
                "Original_Text": "Waktu loading : 18:00\ndriver : M SYAICHONI",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "TWB",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, PKU",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "TIME": "21:00",
                "DATE": "17/2/2026",
                "Original_Text": "Waktu loading : 21:00\ndriver :",
            },
            {
                "UNIT_QTY": "REV",
                "UNIT_TYPE": "",
                "ORIGIN": "",
                "DESTINATION": "",
                "DRIVER": "Rizki",
                "PLATE": "",
                "PHONE": "",
                "TIME": "",
                "DATE": "17/2/2026",
                "Original_Text": "Rev driver unit jam 18:00\ndriver : RIZKI",
            },
        ])

        chat = """
[10.30, 17/2/2026] Admin Rafay:
Rev driver unit jam 18:00
driver : RIZKI
"""
        blocked = mark_order_block(df_raw)
        df_final = enforce_block_quota(blocked)
        out = apply_revisions_from_chat(chat, df_final)

        # Row count tetap mengikuti deklarasi "3 UNIT"
        self.assertEqual(len(out), 3)
        self.assertFalse(out["Original_Text"].str.contains(r"(?i)\b(?:rev|revisi|update)\b", regex=True, na=False).any())
        self.assertEqual(out[out["TIME"] == "18:00"].iloc[0]["DRIVER"], "Rizki")

    def test_revision_header_block_is_not_parsed_as_new_order(self):
        df_raw = pd.DataFrame([
            {
                "UNIT_QTY": "5",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "REQUEST ORDER ONCALL\n06 FEB 2026\n5 UNIT CDDL/24 CBM\nLokasi : ARGOPANTES\nWaktu loading : SEGERA\nRute/tujuan : CGK - JATIM TENTATIF",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Adip",
                "PLATE": "B 3309 AU",
                "PHONE": "+62 852-4568-1444",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "driver  : Adip\nNopol  : B 3309 AU\nNo hp  : +62 852-4568-1444",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Dandan",
                "PLATE": "L 8834 AU",
                "PHONE": "+62 852-8278-1280",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "Rute/tujuan : CGK - JATIM TENTATIF\ndriver  : Dandan\nNopol  : L 8834 AU\nNo hp  : +62 852-8278-1280",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Randy",
                "PLATE": "L 7823 AA",
                "PHONE": "+62 852-8278-8271",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "Rute/tujuan : CGK - JATIM TENTATIF\ndriver  : Randy\nNopol  : L 7823 AA\nNo hp  : +62 852-8278-8271",
            },
            {
                "UNIT_QTY": "5",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "REQUEST ORDER ONCALL\n06 FEB 2026",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Adip",
                "PLATE": "B 3309 AA",
                "PHONE": "+62 852-4568-1444",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "driver  : Adip\nNopol  : B 3309 AA\nNo hp  : +62 852-4568-1444",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Dandan",
                "PLATE": "Z 8934 AB",
                "PHONE": "+62 852-8278-1280",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "Rute/tujuan : CGK - JATIM TENTATIF\ndriver  : Dandan\nNopol  : Z 8934 AB\nNo hp  : +62 852-8278-1280",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK - JATIM TENTATIF",
                "DRIVER": "Randy",
                "PLATE": "L 7823 AA",
                "PHONE": "+62 852-8278-8271",
                "TIME": "",
                "DATE": "06/02/2026",
                "Original_Text": "Rute/tujuan : CGK - JATIM TENTATIF\ndriver  : Randy\nNopol  : L 7823 AA\nNo hp  : +62 852-8278-8271",
            },
            {
                "UNIT_QTY": "",
                "UNIT_TYPE": "",
                "ORIGIN": "",
                "DESTINATION": "",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "TIME": "",
                "DATE": "",
                "Original_Text": "revisi nopol L 8834 AU",
            },
        ])

        chat = """
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 
06 FEB 2026

revisi nopol L 8834 AU
5 UNIT CDDL/24 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF
driver  : Adip
Nopol  : B 3309 AA
No hp  : +62 852-4568-1444

Rute/tujuan : CGK - JATIM TENTATIF
driver  : Dandan
Nopol  : Z 8934 AB
No hp  : +62 852-8278-1280

Rute/tujuan : CGK - JATIM TENTATIF
driver  : Randy
Nopol  : L 7823 AA
No hp  : +62 852-8278-8271
"""

        blocked = mark_order_block(df_raw)
        df_final = enforce_block_quota(blocked)
        self.assertEqual(len(df_final), 4)

        out = apply_revisions_from_chat(chat, df_final)
        self.assertEqual(len(out), 4)
        self.assertEqual(out[out["DRIVER"] == "Dandan"].iloc[0]["PLATE"], "Z 8934 AB")
        self.assertFalse(out["Original_Text"].str.contains(r"(?i)\b(?:rev|revisi|update)\b", regex=True, na=False).any())

    def test_revision_by_time_updates_target_and_keeps_row_count(self):
        df = pd.DataFrame([
            {
                "TIME": "18:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, PKU",
                "UNIT_TYPE": "TWB",
                "DRIVER": "M Syaichoni",
                "PLATE": "N 8872 RK",
                "PHONE": "081231895971",
                "Original_Text": "Waktu loading : 18:00\nRute/tujuan : CGK - PKU",
            },
            {
                "TIME": "21:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, PKU",
                "UNIT_TYPE": "TWB",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "Original_Text": "Waktu loading : 21:00\nRute/tujuan : CGK - PKU",
            },
            {
                "TIME": "",
                "ORIGIN": "",
                "DESTINATION": "",
                "UNIT_TYPE": "",
                "DRIVER": "Rizki",
                "PLATE": "",
                "PHONE": "",
                "Original_Text": "Rev driver unit jam 18:00\ndriver : RIZKI",
            },
        ])

        chat = """
[10.30, 17/2/2026] Admin Rafay:
Rev driver unit jam 18:00
driver : RIZKI
"""
        out = apply_revisions_from_chat(chat, df)

        self.assertEqual(len(out), len(df))
        updated_row = out[out["TIME"] == "18:00"].iloc[0]
        self.assertEqual(updated_row["DRIVER"], "Rizki")

    def test_revision_when_multiple_orders_share_same_time_uses_location(self):
        df = pd.DataFrame([
            {
                "TIME": "18:00",
                "ORIGIN": "MEGAHUB",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Driver A",
                "PLATE": "B 1111 AA",
                "PHONE": "081111111111",
                "Original_Text": "Order A",
            },
            {
                "TIME": "18:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Driver B",
                "PLATE": "B 2222 BB",
                "PHONE": "082222222222",
                "Original_Text": "Order B",
            },
        ])

        chat = """
[11.00, 17/2/2026] Admin Rafay:
Rev driver unit jam 18:00
Lokasi : ARGOPANTES
driver : DODY
"""
        out = apply_revisions_from_chat(chat, df)
        self.assertEqual(len(out), len(df))

        megahub = out[out["ORIGIN"] == "MEGAHUB"].iloc[0]
        argopantes = out[out["ORIGIN"] == "ARGOPANTES"].iloc[0]

        self.assertEqual(megahub["DRIVER"], "Driver A")
        self.assertEqual(argopantes["DRIVER"], "Dody")

    def test_revision_updates_driver_only(self):
        df = pd.DataFrame([
            {
                "TIME": "18:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Old Driver",
                "PLATE": "N 8872 RK",
                "PHONE": "081231895971",
                "Original_Text": "Order X",
            }
        ])

        chat = """
[11.30, 17/2/2026] Admin Rafay:
Revisi driver jam 18:00
driver : RIZKI
"""
        out = apply_revisions_from_chat(chat, df)
        self.assertEqual(len(out), len(df))
        row = out.iloc[0]

        self.assertEqual(row["DRIVER"], "Rizki")
        self.assertEqual(row["PLATE"], "N 8872 RK")
        self.assertEqual(row["PHONE"], "081231895971")

    def test_revision_updates_nopol_only(self):
        df = pd.DataFrame([
            {
                "TIME": "21:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Rizki",
                "PLATE": "N 8872 RK",
                "PHONE": "081231895971",
                "Original_Text": "Order Y",
            }
        ])

        chat = """
[12.00, 17/2/2026] Admin Rafay:
Update nopol unit jam 21:00
Nopol : B 1234 CD
"""
        out = apply_revisions_from_chat(chat, df)
        self.assertEqual(len(out), len(df))
        row = out.iloc[0]

        self.assertEqual(row["PLATE"], "B 1234 CD")
        self.assertEqual(row["DRIVER"], "Rizki")
        self.assertEqual(row["PHONE"], "081231895971")

    def test_revision_updates_phone_only_by_route(self):
        df = pd.DataFrame([
            {
                "TIME": "18:00",
                "ORIGIN": "MEGAHUB",
                "DESTINATION": "CGK, JEPARA",
                "UNIT_TYPE": "CDDL",
                "DRIVER": "Driver A",
                "PLATE": "AD 8517 BA",
                "PHONE": "081000000000",
                "Original_Text": "Order Jepara",
            },
            {
                "TIME": "18:00",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Driver B",
                "PLATE": "B 2222 BB",
                "PHONE": "082000000000",
                "Original_Text": "Order Sub",
            },
        ])

        chat = """
[12.30, 17/2/2026] Admin Rafay:
Update no hp unit
Rute/tujuan : CGK - SUB
No hp : +62 812-3456-7890
"""
        out = apply_revisions_from_chat(chat, df)
        self.assertEqual(len(out), len(df))

        jepara = out[out["DESTINATION"] == "CGK, JEPARA"].iloc[0]
        sub = out[out["DESTINATION"] == "CGK, SUB"].iloc[0]

        self.assertEqual(jepara["PHONE"], "081000000000")
        self.assertEqual(sub["PHONE"], "081234567890")

    def test_data_tambahan_new_order_does_not_refill_its_own_empty_slot(self):
        original_text = """REQUER ORDER  ON CALL
06 MARET 2026
DATA SUMATERA
2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
Nama : Nasip
Nopol : BH 8165 QI
No Tlp :+6281272463920"""

        df = pd.DataFrame([
            {
                "RO_DATE": "06 MARET 2026",
                "DATE": "06 MARET 2026",
                "TIME": "SEGERA",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "PKU",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Nasip",
                "PLATE": "BH 8165 QI",
                "PHONE": "081272463920",
                "Original_Text": original_text,
            },
            {
                "RO_DATE": "06 MARET 2026",
                "DATE": "06 MARET 2026",
                "TIME": "SEGERA",
                "ORIGIN": "ARGOPANTES",
                "DESTINATION": "PKU",
                "UNIT_TYPE": "TWB",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "Original_Text": original_text,
            },
        ])

        class FakeMatcher:
            def rank_candidates(self, query_text, candidates, top_k=10):
                return [
                    {
                        "candidate_index": int(candidates[0]["candidate_index"]),
                        "match_probability": 0.99,
                    }
                ]

        chat = f"Fyi pak data tambahan nya\n{original_text}"
        with patch("app._get_revision_matcher", return_value=FakeMatcher()), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, df)

        self.assertEqual(out["DRIVER"].astype(str).str.contains("Nasip", case=False, na=False).sum(), 1)
        self.assertEqual(out.iloc[1]["DRIVER"], "")
        self.assertEqual(out.iloc[1]["PLATE"], "")
        self.assertEqual(out.iloc[1]["PHONE"], "")

    def test_bare_revision_identity_triplet_updates_existing_order_only(self):
        order_text = """REQUEST ORDER ONCALL 13 MARET 2026:

maaf pak baru masuk info dari megahub
1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 22:00
Rute/tujuan : CGK - DENPASAR
DRVER  :Nanang
No pol  :AB 8053 KA
No hp  :08889693664"""
        revision_text = """REQUEST ORDER ONCALL 13 MARET 2026:

maaf pak baru masuk info dari megahub
1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 22:00
Rute/tujuan : CGK - DENPASAR
REVISI

DRVER  : ADIT
No pol  :AB 2893 KK
No hp  :0888754859"""
        df_raw = pd.DataFrame([
            {
                "UNIT_QTY": "1",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "MEGAHUB",
                "DESTINATION": "CGK, DENPASAR",
                "TIME": "22:00",
                "DATE": "13 MARET 2026",
                "RO_DATE": "13 MARET 2026",
                "DRIVER": "Nanang",
                "PLATE": "AB 8053 KA",
                "PHONE": "08889693664",
                "Original_Text": order_text,
            },
            {
                "UNIT_QTY": "1",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "MEGAHUB",
                "DESTINATION": "CGK, DENPASAR",
                "TIME": "22:00",
                "DATE": "13 MARET 2026",
                "RO_DATE": "13 MARET 2026",
                "DRIVER": "Adit",
                "PLATE": "AB 2893 KK",
                "PHONE": "0888754859",
                "Original_Text": revision_text,
            },
        ])

        class LowConfidenceMatcher:
            def rank_candidates(self, query_text, candidates, top_k=10):
                return [
                    {
                        "candidate_index": int(candidates[0]["candidate_index"]),
                        "match_probability": 0.0001,
                    }
                ]

        chat = f"""
[05.31, 7/3/2026] Akbar Rafay: {order_text}

[05.31, 7/3/2026] Akbar Rafay: {revision_text}
"""
        df_before = enforce_block_quota(mark_order_block(df_raw))
        self.assertEqual(len(df_before), 1)
        self.assertEqual(df_before.iloc[0]["DRIVER"], "Nanang")

        with patch("app._get_revision_matcher", return_value=LowConfidenceMatcher()), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, df_before.copy())

        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertEqual(row["DRIVER"], "Adit")
        self.assertEqual(row["PLATE"], "AB 2893 KK")
        self.assertEqual(row["PHONE"], "0888754859")
        self.assertEqual(row["UNIT_TYPE"], "CDDL")
        self.assertEqual(row["ORIGIN"], "MEGAHUB")
        self.assertEqual(row["DESTINATION"], "CGK, DENPASAR")
        self.assertEqual(row["TIME"], "22:00")

    def test_revision_triplet_prefers_exact_time_row_over_blank_quota_slot(self):
        initial_text = """[05.31, 7/3/2026] Akbar Rafay: Request Unit On Call Tgl 05 Feb 26

2 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/ 06-02-26
Rute/tujuan : CKR-Jateng Tentative
Driver   : Deri
Nopol  : B 878 AA
No Hp  : 6281543674448"""
        revision_text = """[05.31, 7/3/2026] Akbar Rafay: Request Unit On Call Tgl 05 Feb 26

2 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/ 06-02-26
Rute/tujuan : CKR-Jateng Tentative
Revisi
Driver   : Agung
Nopol  : B 555 AX
No Hp  : 628154367433"""
        df_raw = pd.DataFrame([
            {
                "UNIT_QTY": "2",
                "UNIT_TYPE": "CDDL",
                "ORIGIN": "CIKARANG",
                "DESTINATION": "CKR, JATENG TENTATIVE",
                "TIME": "06:00",
                "DATE": "06-02-26",
                "RO_DATE": "05 Feb 26",
                "DRIVER": "Deri",
                "PLATE": "B 878 AA",
                "PHONE": "6281543674448",
                "Original_Text": initial_text,
            }
        ])

        class BlankSlotFirstMatcher:
            def rank_candidates(self, query_text, candidates, top_k=10):
                ranked = sorted(
                    candidates,
                    key=lambda item: int(item["candidate_index"]),
                    reverse=True,
                )
                return [
                    {
                        "candidate_index": int(item["candidate_index"]),
                        "match_probability": 0.99 - (i * 0.01),
                    }
                    for i, item in enumerate(ranked[:top_k])
                ]

        df_before = enforce_block_quota(mark_order_block(df_raw))
        self.assertEqual(len(df_before), 2)
        self.assertEqual(df_before.iloc[0]["DRIVER"], "Deri")
        self.assertEqual(df_before.iloc[1]["DRIVER"], "")

        with patch("app._get_revision_matcher", return_value=BlankSlotFirstMatcher()), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(revision_text, df_before.copy())

        self.assertEqual(len(out), 2)
        self.assertEqual(out.iloc[0]["DRIVER"], "Agung")
        self.assertEqual(out.iloc[0]["PLATE"], "B 555 AX")
        self.assertEqual(out.iloc[0]["PHONE"], "08154367433")
        self.assertEqual(out.iloc[0]["RO_DATE"], "05 Feb 26")
        self.assertEqual(out.iloc[1]["DRIVER"], "")
        self.assertEqual(out.iloc[1]["PLATE"], "")
        self.assertEqual(out.iloc[1]["PHONE"], "")
        self.assertEqual(extract_ro_date_from_text(revision_text), "05 Feb 26")

    def _multi_unit_same_context_df(self):
        return pd.DataFrame([
            {
                "TIME": "22:00",
                "ORIGIN": "CIKARANG",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Andre",
                "PLATE": "L 20374 UU",
                "PHONE": "085739047655",
                "Original_Text": "Order awal unit 1 Andre",
            },
            {
                "TIME": "22:00",
                "ORIGIN": "CIKARANG",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "Dedi",
                "PLATE": "B 2894 AA",
                "PHONE": "081574673448",
                "Original_Text": "Order awal unit 2 Dedi",
            },
            {
                "TIME": "22:00",
                "ORIGIN": "CIKARANG",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "Original_Text": "Order awal partial unit 3",
            },
            {
                "TIME": "22:00",
                "ORIGIN": "CIKARANG",
                "DESTINATION": "CGK, SUB",
                "UNIT_TYPE": "TWB",
                "DRIVER": "",
                "PLATE": "",
                "PHONE": "",
                "Original_Text": "Order awal partial unit 4",
            },
        ])

    def test_enforce_block_quota_ignores_pesan_revisi_label_and_skips_real_revision_block(self):
        initial_text = """Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading : 22:00
Rute/tujuan : CGK-SUB
driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading : 22:00
Rute/tujuan : CGK-SUB
driver : DEDI
Nopol : B 2894 AA
No hp : 081574673448

PESAN REVISI"""
        revision_text = """Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading : 22:00
Rute/tujuan : CGK-SUB
driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading : 22:00
Rute/tujuan : CGK-SUB

REVISI DRIVER
driver : TONO
Nopol : B 5555 XYZ
No hp : 081122223333"""
        df_raw = pd.DataFrame(
            [
                {
                    "UNIT_QTY": "4",
                    "UNIT_TYPE": "TWB",
                    "ORIGIN": "CIKARANG",
                    "DESTINATION": "CGK, SUB",
                    "TIME": "22:00",
                    "DATE": "",
                    "RO_DATE": "09 FEBRUARI 2026",
                    "DRIVER": "Dedi",
                    "PLATE": "B 2894 AA",
                    "PHONE": "081574673448",
                    "Original_Text": initial_text,
                },
                {
                    "UNIT_QTY": "4",
                    "UNIT_TYPE": "TWB",
                    "ORIGIN": "CIKARANG",
                    "DESTINATION": "CGK, SUB",
                    "TIME": "22:00",
                    "DATE": "",
                    "RO_DATE": "09 FEBRUARI 2026",
                    "DRIVER": "Tono",
                    "PLATE": "B 5555 XYZ",
                    "PHONE": "081122223333",
                    "Original_Text": revision_text,
                },
            ]
        )

        out = enforce_block_quota(mark_order_block(df_raw))
        self.assertEqual(len(out), 4)
        self.assertFalse(out["DRIVER"].astype(str).str.contains("Tono", case=False, na=False).any())

    def _apply_with_first_candidate_matcher(self, chat, df):
        class FirstCandidateMatcher:
            def rank_candidates(self, query_text, candidates, top_k=10):
                return [
                    {
                        "candidate_index": int(item["candidate_index"]),
                        "match_probability": 0.99 - (i * 0.01),
                    }
                    for i, item in enumerate(candidates[:top_k])
                ]

        with patch("app._get_revision_matcher", return_value=FirstCandidateMatcher()), patch(
            "app._get_event_classifier", return_value=None
        ):
            return apply_revisions_from_chat(chat, df)

    def test_multi_unit_revision_marker_in_second_segment_updates_second_row(self):
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB

REVISI DRIVER
Driver : TONO
Nopol : B 5555 XYZ
No hp : 081122223333
"""
        out = self._apply_with_first_candidate_matcher(chat, self._multi_unit_same_context_df())

        self.assertEqual(out.iloc[0]["DRIVER"], "Andre")
        self.assertEqual(out.iloc[0]["PLATE"], "L 20374 UU")
        self.assertEqual(out.iloc[1]["DRIVER"], "Tono")
        self.assertEqual(out.iloc[1]["PLATE"], "B 5555 XYZ")
        self.assertEqual(out.iloc[1]["PHONE"], "081122223333")

    def test_multi_unit_revision_marker_in_second_segment_works_without_matcher(self):
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB

REVISI DRIVER
Driver : TONO
Nopol : B 5555 XYZ
No hp : 081122223333
"""
        with patch("app._get_revision_matcher", return_value=None), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, self._multi_unit_same_context_df())

        self.assertEqual(out.iloc[0]["DRIVER"], "Andre")
        self.assertEqual(out.iloc[1]["DRIVER"], "Tono")
        self.assertEqual(out.iloc[1]["PLATE"], "B 5555 XYZ")
        self.assertEqual(out.iloc[1]["PHONE"], "081122223333")

    def test_multi_unit_revision_marker_in_first_segment_updates_first_row(self):
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Revisi
Driver : BUDI
Nopol : L 9999 XX
No hp : 085566778899
Posisi sudah dilokasi muat

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : DEDI
Nopol : B 2894 AA
No hp : 081574673448
"""
        out = self._apply_with_first_candidate_matcher(chat, self._multi_unit_same_context_df())

        self.assertEqual(out.iloc[0]["DRIVER"], "Budi")
        self.assertEqual(out.iloc[0]["PLATE"], "L 9999 XX")
        self.assertEqual(out.iloc[0]["PHONE"], "085566778899")
        self.assertEqual(out.iloc[1]["DRIVER"], "Dedi")
        self.assertEqual(out.iloc[1]["PLATE"], "B 2894 AA")

    def test_multi_unit_revision_old_plate_anchor_updates_matching_row(self):
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

REVISI NOPOL B 2894 AA

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : DEDI
Nopol : B 5678 DD
No hp : 081574673448
"""
        out = self._apply_with_first_candidate_matcher(chat, self._multi_unit_same_context_df())

        self.assertEqual(out.iloc[0]["DRIVER"], "Andre")
        self.assertEqual(out.iloc[0]["PLATE"], "L 20374 UU")
        self.assertEqual(out.iloc[0]["PHONE"], "085739047655")
        self.assertEqual(out.iloc[1]["DRIVER"], "Dedi")
        self.assertEqual(out.iloc[1]["PLATE"], "B 5678 DD")
        self.assertEqual(out.iloc[1]["PHONE"], "081574673448")

    def test_header_old_plate_anchor_updates_matching_row_when_context_repeats(self):
        df = pd.DataFrame(
            [
                {
                    "TIME": "SEGERA",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, SUB",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Driver A",
                    "PLATE": "D 1111 ZZ",
                    "PHONE": "081111111111",
                    "DATE": "06 FEBUARI 2026",
                    "RO_DATE": "06 FEBUARI 2026",
                    "Original_Text": "awal unit lain",
                },
                {
                    "TIME": "SEGERA",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, SUB",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Hendra S.P",
                    "PLATE": "D 9044 AG",
                    "PHONE": "087786676177",
                    "DATE": "06 FEBUARI 2026",
                    "RO_DATE": "06 FEBUARI 2026",
                    "Original_Text": "awal target",
                },
            ]
        )
        chat = """
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 06 FEBUARI 2026

REVISI NOPOL D 9044 AG

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver : HENDRA S.P
Nopol : D 2222 AA
No hp : +62 877-8667-6177
truk lama akinya mati
"""
        with patch("app._get_revision_matcher", return_value=None), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, df)

        self.assertEqual(out.iloc[0]["PLATE"], "D 1111 ZZ")
        self.assertEqual(out.iloc[1]["DRIVER"], "Hendra S.P")
        self.assertEqual(out.iloc[1]["PLATE"], "D 2222 AA")
        self.assertEqual(out.iloc[1]["PHONE"], "087786676177")

    def test_inline_revision_marker_after_existing_identity_extracts_new_middle_unit(self):
        df = pd.DataFrame(
            [
                {
                    "TIME": "SEGERA",
                    "ORIGIN": "MEGAHUB",
                    "DESTINATION": "CGK, JATIM TENTATIF",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Andre",
                    "PLATE": "L 1111 AA",
                    "PHONE": "081111111111",
                    "DATE": "04 FEB 26",
                    "RO_DATE": "04 FEB 26",
                    "Original_Text": "awal unit pertama",
                },
                {
                    "TIME": "SEGERA",
                    "ORIGIN": "MEGAHUB",
                    "DESTINATION": "CGK, JATIM TENTATIF",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Old Middle",
                    "PLATE": "L 2222 BB",
                    "PHONE": "082222222222",
                    "DATE": "04 FEB 26",
                    "RO_DATE": "04 FEB 26",
                    "Original_Text": "awal unit kedua",
                },
            ]
        )
        chat = """
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ULANG ONCALL 04 FEB 26
2 UNIT TWB 50 CBM
Lokasi : MEGAHUB
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF
driver : Andre
Nopol : L 1111 AA
No hp : 081111111111

Rute/tujuan : CGK - JATIM TENTATIF
Revisi
driver : Suparman
Nopol : L 6754 BB
No hp : 082222222222
"""
        with patch("app._get_revision_matcher", return_value=None), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, df)

        self.assertEqual(out.iloc[0]["DRIVER"], "Andre")
        self.assertEqual(out.iloc[0]["PLATE"], "L 1111 AA")
        self.assertEqual(out.iloc[1]["DRIVER"], "Suparman")
        self.assertEqual(out.iloc[1]["PLATE"], "L 6754 BB")
        self.assertEqual(out.iloc[1]["PHONE"], "082222222222")

    def test_noise_before_revision_driver_does_not_drop_payload(self):
        df = pd.DataFrame(
            [
                {
                    "TIME": "SEGERA",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, PKU",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Haryono",
                    "PLATE": "B 1111 AA",
                    "PHONE": "",
                    "DATE": "06 APRIL 2026",
                    "RO_DATE": "06 APRIL 2026",
                    "Original_Text": "awal",
                }
            ]
        )
        chat = """
fyi pak ada perubahan supir
REVISI DRIVER Haryono
Lokasi : ARGOPANTES
Rute/ tuj : CGK - PKU
DRIVER 1 : Slamet
"""
        with patch("app._get_revision_matcher", return_value=None), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revisions_from_chat(chat, df)

        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["DRIVER"], "Slamet")
        self.assertEqual(out.iloc[0]["PLATE"], "B 1111 AA")

    def test_multi_unit_revision_position_prefers_latest_context_group(self):
        older = self._multi_unit_same_context_df()
        older.loc[0, "DRIVER"] = "Old Andre"
        older.loc[0, "PLATE"] = "L 1111 AA"
        older.loc[1, "DRIVER"] = "Old Dedi"
        older.loc[1, "PLATE"] = "B 2222 BB"
        latest = self._multi_unit_same_context_df()
        df = pd.concat([older, latest], ignore_index=True)
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Revisi
Driver : BUDI
Nopol : L 9999 XX
No hp : 085566778899
Posisi sudah dilokasi muat

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : DEDI
Nopol : B 2894 AA
No hp : 081574673448
"""
        out = self._apply_with_first_candidate_matcher(chat, df)

        self.assertEqual(out.iloc[0]["DRIVER"], "Old Andre")
        self.assertEqual(out.iloc[0]["PLATE"], "L 1111 AA")
        self.assertEqual(out.iloc[4]["DRIVER"], "Budi")
        self.assertEqual(out.iloc[4]["PLATE"], "L 9999 XX")
        self.assertEqual(out.iloc[5]["DRIVER"], "Dedi")
        self.assertEqual(out.iloc[5]["PLATE"], "B 2894 AA")

    def test_revision_upload_updates_existing_office_output_without_adding_rows(self):
        existing = pd.DataFrame(
            [
                {
                    "No.": 1,
                    "Job Number": "001/JNE-RAFAY/II/2026",
                    "Tgl RO": "09 FEBRUARI 2026",
                    "Tgl Muat": "09 FEBRUARI 2026",
                    "Pickup": "CIKARANG",
                    "Tujuan": "CGK, SUB",
                    "No. Plat": "L 20374 UU",
                    "Type Truck": "TWB",
                    "Driver": "Andre",
                    "Kontak Driver": "085739047655",
                    "status_unit": "ASSIGNED",
                },
                {
                    "No.": 2,
                    "Job Number": "002/JNE-RAFAY/II/2026",
                    "Tgl RO": "09 FEBRUARI 2026",
                    "Tgl Muat": "09 FEBRUARI 2026",
                    "Pickup": "CIKARANG",
                    "Tujuan": "CGK, SUB",
                    "No. Plat": "B 2894 AA",
                    "Type Truck": "TWB",
                    "Driver": "Dedi",
                    "Kontak Driver": "081574673448",
                    "status_unit": "ASSIGNED",
                },
                {
                    "No.": 3,
                    "Job Number": "003/JNE-RAFAY/II/2026",
                    "Tgl RO": "09 FEBRUARI 2026",
                    "Tgl Muat": "09 FEBRUARI 2026",
                    "Pickup": "CIKARANG",
                    "Tujuan": "CGK, SUB",
                    "No. Plat": "",
                    "Type Truck": "TWB",
                    "Driver": "",
                    "Kontak Driver": "",
                    "status_unit": "PARTIAL",
                },
                {
                    "No.": 4,
                    "Job Number": "004/JNE-RAFAY/II/2026",
                    "Tgl RO": "09 FEBRUARI 2026",
                    "Tgl Muat": "09 FEBRUARI 2026",
                    "Pickup": "CIKARANG",
                    "Tujuan": "CGK, SUB",
                    "No. Plat": "",
                    "Type Truck": "TWB",
                    "Driver": "",
                    "Kontak Driver": "",
                    "status_unit": "PARTIAL",
                },
            ]
        )
        chat = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : ANDRE
Nopol : L 20374 UU
No hp : 085739047655

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB

REVISI DRIVER
Driver : TONO
Nopol : B 5555 XYZ
No hp : 081122223333
"""
        with patch("app._get_revision_matcher", return_value=None), patch(
            "app._get_event_classifier", return_value=None
        ):
            out = apply_revision_to_existing_office_df(chat, existing)

        self.assertIsNotNone(out)
        self.assertEqual(len(out), 4)
        self.assertEqual(out.iloc[0]["Driver"], "Andre")
        self.assertEqual(out.iloc[1]["Driver"], "Tono")
        self.assertEqual(out.iloc[1]["No. Plat"], "B 5555 XYZ")
        self.assertEqual(out.iloc[1]["Kontak Driver"], "081122223333")


if __name__ == "__main__":
    unittest.main()
