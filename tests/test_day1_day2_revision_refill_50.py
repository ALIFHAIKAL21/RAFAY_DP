import sys
import uuid
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.persistence import _match_and_update_existing_row
from models.order_dataset import OrderDataset


def _is_filled(value) -> bool:
    txt = str(value or "").strip().lower()
    return txt not in {"", "-", "null", "none", "nan", "undefined"}


def _norm_text(value: str) -> str:
    return str(value or "").strip().upper()


def _norm_plate(value: str) -> str:
    chars = [c for c in str(value or "").upper() if c.isalnum()]
    return "".join(chars)


class Day1Day2RevisionRefill50Tests(unittest.TestCase):
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

    def _count_status(self, rows):
        assigned = 0
        partial = 0
        unassigned = 0
        for row in rows:
            explicit = _norm_text(row.status_unit)
            if explicit == "ASSIGNED":
                assigned += 1
                continue
            if explicit == "PARTIAL":
                partial += 1
                continue
            if explicit == "UNASSIGNED":
                unassigned += 1
                continue

            filled = sum(
                1
                for value in [
                    row.tgl_ro,
                    row.tgl_muat,
                    row.pickup,
                    row.tujuan,
                    row.no_plat,
                    row.type_truck,
                    row.driver,
                    row.kontak_driver,
                ]
                if _is_filled(value)
            )
            if filled >= 8:
                assigned += 1
            elif filled >= 3:
                partial += 1
            else:
                unassigned += 1
        return assigned, partial, unassigned

    def _build_day1_seed_and_day2_payloads(self):
        # Pola konteks mengikuti chat lapangan: REQUEST ULANG/ONCALL dengan lokasi+rute berulang.
        contexts = [
            ("05 FEBRUARI 2026", "05 FEBRUARI 2026", "CIKOKOL", "CGK, SUB", "TWB"),
            ("05 FEBRUARI 2026", "05 FEBRUARI 2026", "CIKOKOL", "CGK, PKU", "TWB"),
            ("05 FEBRUARI 2026", "05 FEBRUARI 2026", "CIKOKOL", "CGK, MES", "TWB"),
            ("06 FEBRUARI 2026", "06 FEBRUARI 2026", "ARGOPANTES", "CGK, SUB", "TWB"),
            ("06 FEBRUARI 2026", "06 FEBRUARI 2026", "ARGOPANTES", "CGK, JATIM TENTATIF", "CDDL"),
            ("06 FEBRUARI 2026", "06 FEBRUARI 2026", "JNE SUB", "SUB, CGK", "TWB"),
            ("07 FEBRUARI 2026", "07 FEBRUARI 2026", "SEMARANG", "SRG, SUB", "CDDL"),
            ("08 FEBRUARI 2026", "08 FEBRUARI 2026", "ARGOPANTES", "CGK, MES", "TWB"),
            ("09 FEBRUARI 2026", "10 FEBRUARI 2026", "CIKOKOL", "CGK, SUB", "TWB"),
            ("03 MARET 2026", "04 MARET 2026", "ARGOPANTES", "CGK, PKU", "TWB"),
        ]

        day1_rows = []
        day2_refill_payloads = []
        day2_revision_payloads = []
        revision_expectations = []

        for i, (tgl_ro, tgl_muat, pickup, tujuan, type_truck) in enumerate(contexts, start=1):
            base_driver = f"DRIVER DAY1 {i}"
            base_plate = f"B {9100 + i} WX{i:02d}"
            base_phone = f"08194356{i:04d}"

            assigned_row = self._make_row(
                status="ASSIGNED",
                tgl_ro=tgl_ro,
                tgl_muat=tgl_muat,
                pickup=pickup,
                tujuan=tujuan,
                type_truck=type_truck,
                driver=base_driver,
                no_plat=base_plate,
                kontak_driver=base_phone,
            )
            day1_rows.append(assigned_row)

            # Day-2 revisi existing: selang-seling revisi nopol / revisi driver.
            if i % 2 == 0:
                revised_plate = f"BK {8200 + i} VY"
                day2_revision_payloads.append(
                    {
                        "tgl_ro": tgl_ro,
                        "tgl_muat": tgl_muat,
                        "pickup": pickup,
                        "tujuan": tujuan,
                        "type_truck": type_truck,
                        "driver": base_driver.lower(),
                        "no_plat": revised_plate,
                        "kontak_driver": f"+62 {base_phone[1:4]}-{base_phone[4:8]}-{base_phone[8:]}",
                        "status_unit": "ASSIGNED",
                    }
                )
                revision_expectations.append((assigned_row.id, "no_plat", revised_plate))
            else:
                revised_driver = f"REVISI DRIVER {i}"
                day2_revision_payloads.append(
                    {
                        "tgl_ro": tgl_ro,
                        "tgl_muat": tgl_muat,
                        "pickup": pickup,
                        "tujuan": tujuan,
                        "type_truck": type_truck,
                        "driver": revised_driver,
                        "no_plat": base_plate,
                        "kontak_driver": base_phone,
                        "status_unit": "ASSIGNED",
                    }
                )
                revision_expectations.append((assigned_row.id, "driver", revised_driver))

            # 4 slot partial per konteks -> total 40 slot partial.
            for slot in range(1, 5):
                day1_rows.append(
                    self._make_row(
                        status="PARTIAL",
                        tgl_ro=tgl_ro,
                        tgl_muat=tgl_muat,
                        pickup=pickup,
                        tujuan=tujuan,
                        type_truck=type_truck,
                        driver="",
                        no_plat="",
                        kontak_driver="",
                    )
                )
                refill_phone = (
                    f"+62 8{i:02d}{slot:02d}1234567"
                    if slot % 2 == 0
                    else f"08{i:02d}{slot:02d}7654321"
                )
                day2_refill_payloads.append(
                    {
                        "tgl_ro": tgl_ro,
                        "tgl_muat": tgl_muat,
                        "pickup": pickup,
                        "tujuan": tujuan,
                        "type_truck": type_truck,
                        "driver": f"REFILL {i}-{slot}",
                        "no_plat": f"L {9700 + i * 10 + slot} UE",
                        "kontak_driver": refill_phone,
                        "status_unit": "ASSIGNED",
                    }
                )

        return day1_rows, day2_refill_payloads, day2_revision_payloads, revision_expectations

    def test_day1_new_order_50_then_day2_refill_and_revision_existing(self):
        day1_rows, refill_payloads, revision_payloads, revision_expectations = (
            self._build_day1_seed_and_day2_payloads()
        )
        self.assertEqual(len(day1_rows), 50)
        self.assertEqual(len(refill_payloads), 40)
        self.assertEqual(len(revision_payloads), 10)

        before_assigned, before_partial, before_unassigned = self._count_status(day1_rows)
        self.assertEqual(before_assigned, 10)
        self.assertEqual(before_partial, 40)
        self.assertEqual(before_unassigned, 0)

        consumed_ids = set()

        # Day-2 refill partial (REQUEST ULANG ORDER ONCALL style).
        for payload in refill_payloads:
            matched = _match_and_update_existing_row(
                existing_rows=day1_rows,
                incoming_norm=payload,
                is_revision_context=False,
                consumed_ids=consumed_ids,
            )
            self.assertTrue(matched, f"Refill tidak match: {payload}")

        # Day-2 revisi existing (REVISI NOPOL / REVISI DRIVER).
        for payload in revision_payloads:
            matched = _match_and_update_existing_row(
                existing_rows=day1_rows,
                incoming_norm=payload,
                is_revision_context=True,
                consumed_ids=consumed_ids,
            )
            self.assertTrue(matched, f"Revisi tidak match: {payload}")

        self.assertEqual(len(day1_rows), 50)
        self.assertEqual(len(consumed_ids), 50)

        after_assigned, after_partial, after_unassigned = self._count_status(day1_rows)
        self.assertEqual(after_assigned, 50)
        self.assertEqual(after_partial, 0)
        self.assertEqual(after_unassigned, 0)

        for row in day1_rows:
            self.assertTrue(_is_filled(row.driver))
            self.assertTrue(_is_filled(row.no_plat))
            self.assertTrue(_is_filled(row.kontak_driver))

        rows_by_id = {row.id: row for row in day1_rows}
        for row_id, field, expected in revision_expectations:
            row = rows_by_id[row_id]
            actual = getattr(row, field)
            if field == "no_plat":
                self.assertEqual(_norm_plate(actual), _norm_plate(expected))
            else:
                self.assertEqual(_norm_text(actual), _norm_text(expected))


if __name__ == "__main__":
    unittest.main()
