import sys
import uuid
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.persistence import (
    _extract_revision_old_anchors,
    _match_and_update_existing_row,
    _revision_marker_segment_indexes,
)
from models.order_dataset import OrderDataset


class PersistenceMergeTests(unittest.TestCase):
    def _make_row(
        self,
        *,
        status: str,
        tgl_ro: str,
        tgl_muat: str,
        pickup: str,
        tujuan: str,
        type_truck: str,
        driver: str = "",
        no_plat: str = "",
        kontak_driver: str = "",
    ) -> OrderDataset:
        return OrderDataset(
            id=uuid.uuid4(),
            status_unit=status,
            tgl_ro=tgl_ro,
            tgl_muat=tgl_muat,
            pickup=pickup,
            tujuan=tujuan,
            type_truck=type_truck,
            driver=driver,
            no_plat=no_plat,
            kontak_driver=kontak_driver,
        )

    def test_exact_identity_prefers_existing_assigned_over_partial_refill(self):
        assigned = self._make_row(
            status="ASSIGNED",
            tgl_ro="06 FEBRUARI 2026",
            tgl_muat="06 FEBRUARI 2026",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="M. Ibnu",
            no_plat="L 9511 AL",
            kontak_driver="082191633212",
        )
        partial_a = self._make_row(
            status="PARTIAL",
            tgl_ro="",
            tgl_muat="",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )
        partial_b = self._make_row(
            status="PARTIAL",
            tgl_ro="",
            tgl_muat="",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )

        incoming = {
            "tgl_ro": "",
            "tgl_muat": "07 MARET 2026",  # Mismatch tanggal saja (noise parsing)
            "pickup": "ARGOPANTES",
            "tujuan": "CGK, SUB",
            "type_truck": "TWB",
            "driver": "M. iBNU",
            "no_plat": "L 9511 AL",
            "kontak_driver": "082191633212",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned, partial_a, partial_b],
            incoming_norm=incoming,
            is_revision_context=False,
            consumed_ids=consumed_ids,
        )

        self.assertTrue(matched)
        self.assertIn(assigned.id, consumed_ids)
        self.assertEqual((partial_a.driver or "").strip(), "")
        self.assertEqual((partial_a.no_plat or "").strip(), "")
        self.assertEqual((partial_b.driver or "").strip(), "")
        self.assertEqual((partial_b.no_plat or "").strip(), "")

    def test_exact_identity_with_conflicting_context_is_not_forced_match(self):
        assigned = self._make_row(
            status="ASSIGNED",
            tgl_ro="06 FEBRUARI 2026",
            tgl_muat="06 FEBRUARI 2026",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="M. Ibnu",
            no_plat="L 9511 AL",
            kontak_driver="082191633212",
        )

        incoming = {
            "tgl_ro": "07 MARET 2026",
            "tgl_muat": "07 MARET 2026",
            "pickup": "MEGAHUB",
            "tujuan": "CGK, JEPARA",
            "type_truck": "CDDL",
            "driver": "M. iBNU",
            "no_plat": "L 9511 AL",
            "kontak_driver": "082191633212",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned],
            incoming_norm=incoming,
            is_revision_context=False,
            consumed_ids=consumed_ids,
        )

        self.assertFalse(matched)
        self.assertEqual(len(consumed_ids), 0)

    def test_revision_triplet_updates_assigned_row_when_context_unique(self):
        assigned = self._make_row(
            status="ASSIGNED",
            tgl_ro="13 MARET 2026",
            tgl_muat="13 MARET 2026",
            pickup="MEGAHUB",
            tujuan="CGK, DENPASAR",
            type_truck="CDDL",
            driver="Nanang",
            no_plat="AB 8053 KA",
            kontak_driver="08889693664",
        )

        incoming = {
            "tgl_ro": "13 MARET 2026",
            "tgl_muat": "13 MARET 2026",
            "pickup": "MEGAHUB",
            "tujuan": "CGK, DENPASAR",
            "type_truck": "CDDL",
            "driver": "Adit",
            "no_plat": "AB 2893 KK",
            "kontak_driver": "0888754859",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=consumed_ids,
        )

        self.assertTrue(matched)
        self.assertIn(assigned.id, consumed_ids)
        self.assertEqual(assigned.driver, "Adit")
        self.assertEqual(assigned.no_plat, "AB 2893 KK")
        self.assertEqual(assigned.kontak_driver, "0888754859")

    def test_revision_triplet_does_not_update_when_context_is_ambiguous(self):
        assigned_a = self._make_row(
            status="ASSIGNED",
            tgl_ro="13 MARET 2026",
            tgl_muat="13 MARET 2026",
            pickup="MEGAHUB",
            tujuan="CGK, DENPASAR",
            type_truck="CDDL",
            driver="Nanang",
            no_plat="AB 8053 KA",
            kontak_driver="08889693664",
        )
        assigned_b = self._make_row(
            status="ASSIGNED",
            tgl_ro="13 MARET 2026",
            tgl_muat="13 MARET 2026",
            pickup="MEGAHUB",
            tujuan="CGK, DENPASAR",
            type_truck="CDDL",
            driver="Budi",
            no_plat="B 1111 BB",
            kontak_driver="081111111111",
        )

        incoming = {
            "tgl_ro": "13 MARET 2026",
            "tgl_muat": "13 MARET 2026",
            "pickup": "MEGAHUB",
            "tujuan": "CGK, DENPASAR",
            "type_truck": "CDDL",
            "driver": "Adit",
            "no_plat": "AB 2893 KK",
            "kontak_driver": "0888754859",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned_a, assigned_b],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=consumed_ids,
        )

        self.assertFalse(matched)
        self.assertEqual(assigned_a.driver, "Nanang")
        self.assertEqual(assigned_b.driver, "Budi")
        self.assertEqual(len(consumed_ids), 0)

    def test_multi_unit_revision_marker_indexes_follow_unit_segment_position(self):
        first_segment = """
[05.31, 7/3/2026] Akbar Rafay: Request Order Oncall Tgl 09 Feb

4 UNIT TWB
Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Revisi
Driver : BUDI
Nopol : L 9999 XX
No hp : 085566778899

Lokasi  : CIKARANG
Waktu loading  : 22.00
Rute/tujuan : CGK-SUB
Driver : DEDI
Nopol : B 2894 AA
No hp : 081574673448
"""
        second_segment = """
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
        self.assertEqual(_revision_marker_segment_indexes(first_segment), {0})
        self.assertEqual(_revision_marker_segment_indexes(second_segment), {1})

    def test_revision_marker_indexes_ignore_section_label_pesan_revisi(self):
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
Driver : DEDI
Nopol : B 2894 AA
No hp : 081574673448

PESAN REVISI
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
        self.assertEqual(_revision_marker_segment_indexes(chat), {3})

    def test_extract_revision_old_plate_anchor_from_header(self):
        chat = """
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 06 FEBUARI 2026

REVISI NOPOL D 9044 AG

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver : HENDRA S.P
Nopol : D 1111 AA
"""

        self.assertEqual(_extract_revision_old_anchors(chat), {"no_plat": "D9044AG"})

    def test_revision_old_plate_anchor_updates_matching_row_when_static_context_repeats(self):
        other = self._make_row(
            status="ASSIGNED",
            tgl_ro="06 FEBUARI 2026",
            tgl_muat="06 FEBUARI 2026",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Driver A",
            no_plat="D 1111 ZZ",
            kontak_driver="081111111111",
        )
        target = self._make_row(
            status="ASSIGNED",
            tgl_ro="06 FEBUARI 2026",
            tgl_muat="06 FEBUARI 2026",
            pickup="ARGOPANTES",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Hendra S.P",
            no_plat="D 9044 AG",
            kontak_driver="087786676177",
        )
        incoming = {
            "tgl_ro": "06 FEBUARI 2026",
            "tgl_muat": "06 FEBUARI 2026",
            "pickup": "ARGOPANTES",
            "tujuan": "CGK, SUB",
            "type_truck": "TWB",
            "driver": "HENDRA S.P",
            "no_plat": "D 2222 AA",
            "kontak_driver": "087786676177",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[other, target],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=consumed_ids,
            revision_old_anchors={"no_plat": "D9044AG"},
        )

        self.assertTrue(matched)
        self.assertEqual(other.no_plat, "D 1111 ZZ")
        self.assertEqual(target.no_plat, "D 2222 AA")
        self.assertEqual(target.driver, "HENDRA S.P")
        self.assertIn(target.id, consumed_ids)

    def test_full_armada_replacement_uses_static_context_with_short_year_date(self):
        assigned = self._make_row(
            status="ASSIGNED",
            tgl_ro="08 JANUARI 2026",
            tgl_muat="08 JANUARI 2026",
            pickup="CIKOKOL + CIKARANG",
            tujuan="CGK, JL PERAK SURABAYA, PT BM",
            type_truck="CDDL",
            driver="M. Ibnu",
            no_plat="L 9511 AL",
            kontak_driver="082191633212",
        )
        incoming = {
            "tgl_ro": "08 JAN 26",
            "tgl_muat": "08 JAN 26",
            "pickup": "CIKOKOL + CIKARANG",
            "tujuan": "CGK, JL PERAK SURABAYA, PT BM",
            "type_truck": "CDDL",
            "driver": "Agus Riyanto",
            "no_plat": "L 2233 BB",
            "kontak_driver": "083333333333",
            "status_unit": "ASSIGNED",
        }

        matched = _match_and_update_existing_row(
            existing_rows=[assigned],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=set(),
        )

        self.assertTrue(matched)
        self.assertEqual(assigned.driver, "Agus Riyanto")
        self.assertEqual(assigned.no_plat, "L 2233 BB")
        self.assertEqual(assigned.kontak_driver, "083333333333")

    def test_multi_unit_revision_position_updates_first_assigned_row(self):
        assigned_a = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Andre",
            no_plat="L 20374 UU",
            kontak_driver="085739047655",
        )
        assigned_b = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Dedi",
            no_plat="B 2894 AA",
            kontak_driver="081574673448",
        )
        incoming = {
            "tgl_ro": "09 FEBRUARI 2026",
            "tgl_muat": "09 FEBRUARI 2026",
            "pickup": "CIKARANG",
            "tujuan": "CGK, SUB",
            "type_truck": "TWB",
            "driver": "Budi",
            "no_plat": "L 9999 XX",
            "kontak_driver": "085566778899",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned_a, assigned_b],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=consumed_ids,
            revision_segment_index=0,
        )

        self.assertTrue(matched)
        self.assertEqual(assigned_a.driver, "Budi")
        self.assertEqual(assigned_a.no_plat, "L 9999 XX")
        self.assertEqual(assigned_a.kontak_driver, "085566778899")
        self.assertEqual(assigned_b.driver, "Dedi")
        self.assertIn(assigned_a.id, consumed_ids)

    def test_multi_unit_revision_position_updates_second_assigned_row(self):
        assigned_a = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Andre",
            no_plat="L 20374 UU",
            kontak_driver="085739047655",
        )
        assigned_b = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Dedi",
            no_plat="B 2894 AA",
            kontak_driver="081574673448",
        )
        incoming = {
            "tgl_ro": "09 FEBRUARI 2026",
            "tgl_muat": "09 FEBRUARI 2026",
            "pickup": "CIKARANG",
            "tujuan": "CGK, SUB",
            "type_truck": "TWB",
            "driver": "Tono",
            "no_plat": "B 5555 XYZ",
            "kontak_driver": "081122223333",
            "status_unit": "ASSIGNED",
        }

        consumed_ids = set()
        matched = _match_and_update_existing_row(
            existing_rows=[assigned_a, assigned_b],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=consumed_ids,
            revision_segment_index=1,
        )

        self.assertTrue(matched)
        self.assertEqual(assigned_a.driver, "Andre")
        self.assertEqual(assigned_a.no_plat, "L 20374 UU")
        self.assertEqual(assigned_b.driver, "Tono")
        self.assertEqual(assigned_b.no_plat, "B 5555 XYZ")
        self.assertEqual(assigned_b.kontak_driver, "081122223333")
        self.assertIn(assigned_b.id, consumed_ids)

    def test_multi_unit_revision_position_prefers_latest_context_group(self):
        old_a = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Old Andre",
            no_plat="L 1111 AA",
            kontak_driver="081111111111",
        )
        old_b = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Old Dedi",
            no_plat="B 2222 BB",
            kontak_driver="082222222222",
        )
        old_p1 = self._make_row(
            status="PARTIAL",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )
        old_p2 = self._make_row(
            status="PARTIAL",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )
        new_a = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Andre",
            no_plat="L 20374 UU",
            kontak_driver="085739047655",
        )
        new_b = self._make_row(
            status="ASSIGNED",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
            driver="Dedi",
            no_plat="B 2894 AA",
            kontak_driver="081574673448",
        )
        new_p1 = self._make_row(
            status="PARTIAL",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )
        new_p2 = self._make_row(
            status="PARTIAL",
            tgl_ro="09 FEBRUARI 2026",
            tgl_muat="09 FEBRUARI 2026",
            pickup="CIKARANG",
            tujuan="CGK, SUB",
            type_truck="TWB",
        )
        incoming = {
            "tgl_ro": "09 FEBRUARI 2026",
            "tgl_muat": "09 FEBRUARI 2026",
            "pickup": "CIKARANG",
            "tujuan": "CGK, SUB",
            "type_truck": "TWB",
            "driver": "Budi",
            "no_plat": "L 9999 XX",
            "kontak_driver": "085566778899",
            "status_unit": "ASSIGNED",
        }

        matched = _match_and_update_existing_row(
            existing_rows=[old_a, old_b, old_p1, old_p2, new_a, new_b, new_p1, new_p2],
            incoming_norm=incoming,
            is_revision_context=True,
            consumed_ids=set(),
            revision_segment_index=0,
            revision_group_size=4,
        )

        self.assertTrue(matched)
        self.assertEqual(old_a.driver, "Old Andre")
        self.assertEqual(old_a.no_plat, "L 1111 AA")
        self.assertEqual(new_a.driver, "Budi")
        self.assertEqual(new_a.no_plat, "L 9999 XX")
        self.assertEqual(new_b.driver, "Dedi")


if __name__ == "__main__":
    unittest.main()
