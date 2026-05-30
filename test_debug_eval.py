"""Debug: trace the evaluation pipeline for ATURAN 1 test case."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")

from audit_dashboard import (
    _compute_ml_observability,
    _extract_expected_slots,
    _prepare_rows_for_matching,
    _pair_expected_slots,
    _detect_duplicate_rows,
    extract_ground_truth_entities,
)
import pandas as pd

test_msg = (
    "[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ULANG ONCALL\n"
    "06 FEB 2026\n\n"
    "10 UNIT CDDL/24 CBM\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : SEGERA\n"
    "Rute/tujuan : CGK - JATIM TENTATIF\n"
    "driver  :\n"
    "Nopol  :\n"
    "No hp  :\n"
)

expected_rows = 1

# Step 1: Expected slots
expected_slots = _extract_expected_slots(test_msg, expected_rows)
print(f"Expected slots: {len(expected_slots)}")
for i, s in enumerate(expected_slots):
    print(f"  [{i}] status={s.get('status')} driver_key={s.get('driver_key')!r} "
          f"plate_key={s.get('plate_key')!r} route_key={s.get('route_key')!r} "
          f"pickup_key={s.get('pickup_key')!r}")

# Step 2: Model output
model_row = pd.DataFrame([{
    "tgl_ro": "06 FEBRUARI 2026",
    "tgl_muat": "06 FEBRUARI 2026",
    "pickup": "ARGOPANTES",
    "tujuan": "CGK - JATIM TENTATIF",
    "type_truck": "CDDL",
    "driver": "",
    "no_plat": "",
    "kontak_driver": "",
    "status_unit": "PARTIAL",
}])

# Step 3: Prepare rows
prepared = _prepare_rows_for_matching(model_row)
prepared["_audit_row_no"] = list(range(1, len(prepared) + 1))
print(f"\nPrepared rows: {len(prepared)}")
for idx, row in prepared.iterrows():
    print(f"  [{idx}] driver_key={row.get('driver_key')!r} plate_key={row.get('plate_key')!r} "
          f"status_norm={row.get('status_norm')!r} route_key={row.get('route_key')!r}")

# Step 4: Detect duplicates
dup = _detect_duplicate_rows(prepared)
print(f"\nDuplicates: {dup}")

# Step 5: Pair slots
pairs, unmatched = _pair_expected_slots(expected_slots, prepared, dup)
print(f"\nPairs: {len(pairs)}, Unmatched: {len(unmatched)}")
for p in pairs:
    print(f"  Pair: slot={p['slot'].get('slot_id')} -> row_idx={p['row_idx']}")
for u in unmatched:
    print(f"  Unmatched: slot={u.get('slot_id')} status={u.get('status')}")

# Step 6: Compute full observability
audit = _compute_ml_observability(test_msg, expected_rows, model_row)
print(f"\nRecord: tp={audit['record']['tp']} fp={audit['record']['fp']} fn={audit['record']['fn']}")
sf = audit.get("slot_fields", {})
if sf:
    for field, counts in sf.items():
        print(f"  {field:15s}: tp={counts['tp']} fp={counts['fp']} fn={counts['fn']}")
else:
    print("  No slot_fields in audit!")
