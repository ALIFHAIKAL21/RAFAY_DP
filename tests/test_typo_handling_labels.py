import unittest
import pandas as pd

from app import (
    auto_format_chat_input,
    apply_revisions_from_chat,
    extract_driver_pair_from_text,
    extract_loading_details,
    extract_origin_from_text,
    extract_route_from_text,
)


class TypoHandlingLabelTests(unittest.TestCase):
    def test_typo_labels_are_normalized_for_core_fields(self):
        text = """
5 UNIT TWB 50 CBM
Loksai : ARGOPANTES
Wktu lodaing : 17:00/05-03-2026
Rute/tujan : CGK - SUB
drver : Iwan Hariono
Nopool : BL 8188 JP
No Hpp :081389976421
""".strip()

        formatted = auto_format_chat_input(text)
        self.assertIn("Lokasi : ARGOPANTES", formatted)
        self.assertIn("Waktu loading : 17:00", formatted)
        self.assertIn("Rute/tujuan : CGK - SUB", formatted)
        self.assertIn("driver :", formatted)
        self.assertIn("Nopol :", formatted)
        self.assertIn("No hp :", formatted)

        self.assertEqual(extract_origin_from_text(text), "ARGOPANTES")
        self.assertIn("CGK", extract_route_from_text(text).upper())
        self.assertIn("SUB", extract_route_from_text(text).upper())

        details = extract_loading_details(text)
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]["time"], "17:00")
        self.assertEqual(details[0]["driver"], "Iwan Hariono")
        self.assertEqual(details[0]["plate"], "BL 8188 JP")
        self.assertEqual(details[0]["phone"], "081389976421")

    def test_driver_pair_with_typo_driver_labels(self):
        text = """
drver 1 : Edi Setiawan
Drver2 : Jatmiyanta
""".strip()
        d1, d2 = extract_driver_pair_from_text(text)
        self.assertEqual(d1, "Edi Setiawan")
        self.assertEqual(d2, "Jatmiyanta")

    def test_revision_payload_accepts_typo_labels(self):
        df = pd.DataFrame(
            [
                {
                    "TIME": "17:00",
                    "ORIGIN": "ARGOPANTES",
                    "DESTINATION": "CGK, SUB",
                    "UNIT_TYPE": "TWB",
                    "DRIVER": "Old Driver",
                    "PLATE": "BL 8188 JP",
                    "PHONE": "081389976421",
                    "Original_Text": "Order awal",
                }
            ]
        )
        chat = """
[10.30, 05/03/2026] Admin Rafay:
Revisi drver jam 17:00
Loksai : ARGOPANTES
drver : RIZKI
Nopool : B 1234 CD
No Hpp : 0812-1111-2222
""".strip()

        out = apply_revisions_from_chat(chat, df)
        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertEqual(row["DRIVER"], "Rizki")
        self.assertEqual(row["PLATE"], "B 1234 CD")
        self.assertEqual(row["PHONE"], "081211112222")


if __name__ == "__main__":
    unittest.main()

