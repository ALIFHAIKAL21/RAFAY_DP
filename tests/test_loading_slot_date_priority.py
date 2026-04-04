import unittest

import pandas as pd

from app import auto_format_chat_input, enforce_block_quota, extract_loading_candidates


def _base_text(order_specific_first=True):
    if order_specific_first:
        slot_1 = """
Waktu loading : 07:00 07/02/2026
Rute/tujuan : CGK - PDG
driver : SUTRISNO
Nopol : BM 8364 AU
No hp : 085353886066
""".strip()
        slot_2 = """
Waktu loading : SEGERA 04/02/2026
Rute/tujuan : CGK - PDG
driver : ZAINUL
Nopol : BM 8364 AU
No hp : 085353886066
""".strip()
    else:
        slot_1 = """
Waktu loading : SEGERA 04/02/2026
Rute/tujuan : CGK - PDG
driver : SUTRISNO
Nopol : BM 8364 AU
No hp : 085353886066
""".strip()
        slot_2 = """
Waktu loading : 07:00 07/02/2026
Rute/tujuan : CGK - PDG
driver : ZAINUL
Nopol : BM 8364 AU
No hp : 085353886066
""".strip()

    return f"""
REQUEST ORDER ONCALL 04/02/2026
2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
{slot_1}
{slot_2}
""".strip()


class LoadingSlotDatePriorityTests(unittest.TestCase):
    def _build_df(self, original_text):
        return pd.DataFrame(
            [
                {
                    "BLOCK_ID": 1,
                    "UNIT_QTY": "2",
                    "UNIT_TYPE": "TWB",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, PDG",
                    "DRIVER": "Sutrisno",
                    "PLATE": "BM 8364 AU",
                    "PHONE": "085353886066",
                    "TIME": "",
                    "DATE": "07/02/2026",
                    "RO_DATE": "04/02/2026",
                    "Original_Text": original_text,
                },
                {
                    "BLOCK_ID": 1,
                    "UNIT_QTY": "",
                    "UNIT_TYPE": "TWB",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, PDG",
                    "DRIVER": "Zainul",
                    "PLATE": "BM 8364 AU",
                    "PHONE": "085353886066",
                    "TIME": "",
                    "DATE": "07/02/2026",
                    "RO_DATE": "04/02/2026",
                    "Original_Text": original_text,
                },
            ]
        )

    def test_specific_then_segera_keeps_second_row_ro_date(self):
        df = self._build_df(_base_text(order_specific_first=True))
        out = enforce_block_quota(df)
        self.assertEqual(len(out), 2)

        # Urutan slot teks asli harus menang: [07/02/2026, 04/02/2026]
        self.assertEqual(str(out.iloc[0]["DATE"]).strip(), "07/02/2026")
        self.assertEqual(str(out.iloc[1]["DATE"]).strip(), "04/02/2026")

    def test_segera_then_specific_keeps_second_row_specific_date(self):
        df = self._build_df(_base_text(order_specific_first=False))
        out = enforce_block_quota(df)
        self.assertEqual(len(out), 2)

        # Urutan slot teks asli harus menang: [04/02/2026, 07/02/2026]
        self.assertEqual(str(out.iloc[0]["DATE"]).strip(), "04/02/2026")
        self.assertEqual(str(out.iloc[1]["DATE"]).strip(), "07/02/2026")

    def test_date_only_then_segera_without_date_keeps_ro_on_second_slot(self):
        original_text = """
REQUEST ORDER ONCALL 04/02/2026
2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : 05/02/2026
Rute/tujuan : CGK - PDG
driver : SUTRISNO
Nopol : BM 8364 AU
No hp : 085353886066

Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - PDG
driver : ZAINUL
Nopol : BM 8364 AU
No hp : 085353886066
""".strip()

        df = self._build_df(original_text)
        out = enforce_block_quota(df)
        self.assertEqual(len(out), 2)

        # Slot 1 = tanggal spesifik, Slot 2 = SEGERA -> ikut Tgl RO.
        self.assertEqual(str(out.iloc[0]["DATE"]).strip(), "05/02/2026")
        self.assertEqual(str(out.iloc[1]["DATE"]).strip(), "04/02/2026")

    def test_date_only_loading_does_not_override_next_segera_context(self):
        raw_text = """
Akbar Rafay: Request Unit On Call 04 FEBUARI 2026

RAFAY
2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 05/02/2026
Rute/tujuan : CGK- PDG
driver  : SUTRISNO
Nopol  : BM 8364 AU
No hp  :0853-5388-6066

Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK- PDG
driver  : ZAINUL
Nopol  : BM 8364 AU
No hp  :0853-5388-6066
""".strip()
        formatted = auto_format_chat_input(raw_text)
        self.assertIn("Waktu loading : 05/02/2026", formatted)
        self.assertNotIn("Waktu loading :\nRute/tujuan", formatted)

        candidates = extract_loading_candidates(formatted)
        self.assertGreaterEqual(len(candidates), 2)
        self.assertEqual(str(candidates[0].get("date", "")).strip(), "05/02/2026")
        # Slot SEGERA kedua harus ikut context header (04 FEBUARI 2026), bukan 05/02/2026.
        self.assertEqual(str(candidates[1].get("date", "")).strip().upper(), "04 FEBUARI 2026")


if __name__ == "__main__":
    unittest.main()
