import sys
import uuid
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.persistence import _match_and_update_existing_row
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


if __name__ == "__main__":
    unittest.main()
