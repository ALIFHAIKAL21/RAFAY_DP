import unittest
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import apply_driver_pair_from_text, enforce_block_quota, mark_order_block


class SingleLoadingMultiIdentityTests(unittest.TestCase):
    def _build_df(self, original_text: str):
        return pd.DataFrame(
            [
                {
                    "UNIT_QTY": "6",
                    "UNIT_TYPE": "WB",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, SUB",
                    "DRIVER": "Rosyit",
                    "PLATE": "B 9562 TEU",
                    "PHONE": "082313572678",
                    "TIME": "23:00",
                    "DATE": "03/03/2026",
                    "RO_DATE": "03/03/2026",
                    "Original_Text": original_text,
                }
            ]
        )

    def _extract_assigned_rows(self, df_final: pd.DataFrame) -> pd.DataFrame:
        out = df_final.copy()
        for col in ["DRIVER", "PLATE", "PHONE"]:
            out[col] = out[col].fillna("").astype(str).str.strip()
        return out[(out["DRIVER"] != "") & (out["PLATE"] != "") & (out["PHONE"] != "")]

    def test_single_loading_two_driver_blocks_fills_two_units(self):
        original_text = """
REQUEST  ORDER  ONCALL  3 MARET 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES
Waktu loading : 23:00
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  : 082313572678

Driver : sofyan
Nopol : B 9679WT
No Hp : 082231837381
""".strip()

        df_raw = self._build_df(original_text)
        df_blocked = mark_order_block(df_raw)
        df_final = enforce_block_quota(df_blocked)

        self.assertEqual(len(df_final), 6)

        assigned = self._extract_assigned_rows(df_final)
        self.assertEqual(len(assigned), 2)

        drivers_upper = set(assigned["DRIVER"].str.upper().tolist())
        self.assertIn("ROSYIT", drivers_upper)
        self.assertIn("SOFYAN", drivers_upper)

        plate_text = " ".join(assigned["PLATE"].str.upper().tolist())
        self.assertIn("9562", plate_text)
        self.assertIn("9679", plate_text)

    def test_single_loading_single_driver_still_one_assigned(self):
        original_text = """
REQUEST  ORDER  ONCALL  3 MARET 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES
Waktu loading : 23:00
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  : 082313572678
""".strip()

        df_raw = self._build_df(original_text)
        df_blocked = mark_order_block(df_raw)
        df_final = enforce_block_quota(df_blocked)

        self.assertEqual(len(df_final), 6)

        assigned = self._extract_assigned_rows(df_final)
        self.assertEqual(len(assigned), 1)
        self.assertEqual(assigned.iloc[0]["DRIVER"].upper(), "ROSYIT")

    def test_numbered_driver_pair_single_plate_is_one_assigned_unit(self):
        original_text = """
REQUEST ORDER ONCAL
06 APRIL 2026

3 unit TWB 50 Cbm
Lokasi : CIKOKOL
Rute/ tuj : CGK - PKU
Waktu loading : SEGERA
RAFAY
DRIVER 1 :  Otong
DRIVER 2 :  Tarman
NOPOL    : B 7370 SJF
NOHP      :081234000010
""".strip()

        df_raw = pd.DataFrame(
            [
                {
                    "UNIT_QTY": "3",
                    "UNIT_TYPE": "TWB",
                    "ORIGIN": "CIKOKOL",
                    "DESTINATION": "CGK, PKU",
                    "DRIVER": "Otong",
                    "PLATE": "B 7370 SJF",
                    "PHONE": "081234000010",
                    "TIME": "SEGERA",
                    "DATE": "06/04/2026",
                    "RO_DATE": "06/04/2026",
                    "Original_Text": original_text,
                }
            ]
        )

        df_final = enforce_block_quota(mark_order_block(df_raw))
        df_final = apply_driver_pair_from_text(df_final)

        self.assertEqual(len(df_final), 3)
        assigned = self._extract_assigned_rows(df_final)
        self.assertEqual(len(assigned), 1)
        self.assertEqual(assigned.iloc[0]["DRIVER"], "Otong & Tarman")
        self.assertEqual(assigned.iloc[0]["PLATE"], "B 7370 SJF")
        self.assertEqual(
            int((df_final["PLATE"].fillna("").astype(str).str.upper() == "B 7370 SJF").sum()),
            1,
        )


if __name__ == "__main__":
    unittest.main()
