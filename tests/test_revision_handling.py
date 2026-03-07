import unittest
import pandas as pd

from app import apply_revisions_from_chat, mark_order_block, enforce_block_quota


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


if __name__ == "__main__":
    unittest.main()
