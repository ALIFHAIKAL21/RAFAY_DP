"""Test the EVALUATOR scoring logic: ATURAN 1 (driver spill-over) & ATURAN 2 (tgl_muat hierarchy).

These tests simulate what happens when the model output is compared against
the ground truth.  We verify that the evaluator correctly scores TP/FP/FN
for each field, respecting the business rules.
"""
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")

from audit_dashboard import (
    _is_spilled_label,
    _sanitize_driver_value,
    _compute_slot_field_metrics,
    extract_ground_truth_entities,
    _extract_expected_slots,
    _prepare_rows_for_matching,
    _pair_expected_slots,
    _detect_duplicate_rows,
    _compute_ml_observability,
    _normalize_compact,
    _parse_indonesian_date,
)
import pandas as pd


print("=" * 60)
print("TEST SUITE: Evaluator Scoring Logic")
print("=" * 60)

# ─── TEST 1: _is_spilled_label detection ───
print("\n=== TEST 1: Spill-over Label Detection ===")
assert _is_spilled_label("Nopol :") == True, "Should detect 'Nopol :' as label"
assert _is_spilled_label("Nopol") == True, "Should detect 'Nopol' as label"
assert _is_spilled_label("No hp  :") == True, "Should detect 'No hp  :' as label"
assert _is_spilled_label("no Hp") == True, "Should detect 'no Hp' as label"
assert _is_spilled_label(" : ") == True, "Should detect ' : ' as empty"
assert _is_spilled_label("") == True, "Should detect '' as empty"
assert _is_spilled_label("lokasi") == True, "Should detect 'lokasi' as label"
assert _is_spilled_label("SUTRISNO") == False, "Should NOT detect 'SUTRISNO' as label"
assert _is_spilled_label("B 9563 TEU") == False, "Should NOT detect plate as label"
assert _is_spilled_label("0812345678") == False, "Should NOT detect phone as label"
assert _is_spilled_label("Edi setiawan") == False, "Should NOT detect name as label"
assert _is_spilled_label("A. Sukur") == False, "Should NOT detect name with period as label"
print("  >> All spill-over detections PASSED!")

# ─── TEST 2: _sanitize_driver_value ───
print("\n=== TEST 2: Driver Sanitization ===")
assert _sanitize_driver_value("Nopol :") == "", "Spill-over should become empty"
assert _sanitize_driver_value("  Nopol  ") == "", "Spill-over with spaces should become empty"
assert _sanitize_driver_value("") == "", "Empty should stay empty"
assert _sanitize_driver_value("SUTRISNO") == "SUTRISNO", "Valid name should be preserved"
assert _sanitize_driver_value("  Edi setiawan  ") == "Edi setiawan", "Valid name should be trimmed"
print("  >> All driver sanitizations PASSED!")


# ─── TEST 3: ATURAN 1 — Evaluator correctly handles empty driver as TP ───
print("\n=== TEST 3: ATURAN 1 — Empty Driver = PARTIAL (Correct TP) ===")
# Simulate: input has empty driver, model correctly outputs driver="" + status="PARTIAL"
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

gt = extract_ground_truth_entities(test_msg)
assert gt[0]["driver"] == "", f"GT driver should be empty, got [{gt[0]['driver']}]"
assert gt[0]["status_unit"] == "PARTIAL", f"GT status should be PARTIAL, got [{gt[0]['status_unit']}]"

# Simulate model output that correctly predicts empty driver + PARTIAL
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

audit = _compute_ml_observability(test_msg, 1, model_row)
sf = audit.get("slot_fields", {})

print(f"  driver   TP={sf.get('driver', {}).get('tp', 0)}  FP={sf.get('driver', {}).get('fp', 0)}  FN={sf.get('driver', {}).get('fn', 0)}")
print(f"  status   TP={sf.get('status_unit', {}).get('tp', 0)}  FP={sf.get('status_unit', {}).get('fp', 0)}  FN={sf.get('status_unit', {}).get('fn', 0)}")
assert sf["driver"]["tp"] == 1, f"ATURAN 1 FAIL: driver TP should be 1, got {sf['driver']['tp']}"
assert sf["driver"]["fp"] == 0, f"ATURAN 1 FAIL: driver FP should be 0, got {sf['driver']['fp']}"
assert sf["driver"]["fn"] == 0, f"ATURAN 1 FAIL: driver FN should be 0, got {sf['driver']['fn']}"
assert sf["status_unit"]["tp"] == 1, f"ATURAN 1 FAIL: status TP should be 1, got {sf['status_unit']['tp']}"
print("  >> ATURAN 1 — Empty driver correctly scored as TP!")


# ─── TEST 4: ATURAN 2A — Time only → tgl_muat = tgl_ro ───
print("\n=== TEST 4: ATURAN 2A — Time Only → tgl_muat = tgl_ro ===")
test_msg_2a = (
    "[08.06, 10/3/2026] Akbar Rafay: Request Unit On Call Tgl 12 MARET 2026\n\n"
    "3 UNIT TWB 50 CBM\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : 21:00\n"
    "Rute/tujuan : CGK - DPS\n"
    "driver  : M SYAICHONI\n"
    "Nopol  : N 8872 RK\n"
    "No hp  : 081231895971\n"
)

gt_2a = extract_ground_truth_entities(test_msg_2a)
assert gt_2a[0]["tgl_muat"] == "12 MARET 2026", f"GT tgl_muat should be '12 MARET 2026', got [{gt_2a[0]['tgl_muat']}]"

# Model correctly outputs tgl_muat = tgl_ro (same as GT)
model_2a = pd.DataFrame([{
    "tgl_ro": "12 MARET 2026",
    "tgl_muat": "12 MARET 2026",
    "pickup": "ARGOPANTES",
    "tujuan": "CGK - DPS",
    "type_truck": "TWB",
    "driver": "M SYAICHONI",
    "no_plat": "N 8872 RK",
    "kontak_driver": "081231895971",
    "status_unit": "ASSIGNED",
}])

audit_2a = _compute_ml_observability(test_msg_2a, 1, model_2a)
sf_2a = audit_2a.get("slot_fields", {})
print(f"  tgl_muat TP={sf_2a['tgl_muat']['tp']}  FP={sf_2a['tgl_muat']['fp']}  FN={sf_2a['tgl_muat']['fn']}")
assert sf_2a["tgl_muat"]["tp"] == 1, f"ATURAN 2A FAIL: tgl_muat TP should be 1"
assert sf_2a["tgl_muat"]["fp"] == 0, f"ATURAN 2A FAIL: tgl_muat FP should be 0"
print("  >> ATURAN 2A PASSED!")


# ─── TEST 5: ATURAN 2B — Explicit date in Waktu Loading ───
print("\n=== TEST 5: ATURAN 2B — Explicit Date → Different tgl_muat ===")
test_msg_2b = (
    "[08.05, 10/3/2026] Akbar Rafay: Request Unit On Call Tgl 12 MARET 2026\n\n"
    "3 UNIT CDDL 24 CBM\n"
    "Lokasi : CIKARANG\n"
    "Waktu loading : 06:00/13-03-26\n"
    "Rute/tujuan : CKR - JATIM TENTATIVE\n"
    "driver  : JATMIYANTA\n"
    "Nopol  : F 9648 TH\n"
    "No hp  : 082118558105\n"
)

gt_2b = extract_ground_truth_entities(test_msg_2b)
assert gt_2b[0]["tgl_muat"] == "13 MARET 2026", f"GT tgl_muat should be '13 MARET 2026', got [{gt_2b[0]['tgl_muat']}]"

# Model correctly outputs the explicit date
model_2b = pd.DataFrame([{
    "tgl_ro": "12 MARET 2026",
    "tgl_muat": "13 MARET 2026",
    "pickup": "CIKARANG",
    "tujuan": "CKR - JATIM TENTATIVE",
    "type_truck": "CDDL",
    "driver": "JATMIYANTA",
    "no_plat": "F 9648 TH",
    "kontak_driver": "082118558105",
    "status_unit": "ASSIGNED",
}])

audit_2b = _compute_ml_observability(test_msg_2b, 1, model_2b)
sf_2b = audit_2b.get("slot_fields", {})
print(f"  tgl_muat TP={sf_2b['tgl_muat']['tp']}  FP={sf_2b['tgl_muat']['fp']}  FN={sf_2b['tgl_muat']['fn']}")
assert sf_2b["tgl_muat"]["tp"] == 1, f"ATURAN 2B FAIL: tgl_muat TP should be 1"
assert sf_2b["tgl_muat"]["fp"] == 0, f"ATURAN 2B FAIL: tgl_muat FP should be 0"
print("  >> ATURAN 2B PASSED!")


# ─── TEST 6: ATURAN 2B — Model uses wrong date → should get FP + FN ───
print("\n=== TEST 6: ATURAN 2B — Model uses WRONG date → FP/FN ===")
# Same input as test 5, but model incorrectly uses tgl_ro instead of explicit date
model_2b_wrong = pd.DataFrame([{
    "tgl_ro": "12 MARET 2026",
    "tgl_muat": "12 MARET 2026",  # WRONG: should be 13 MARET 2026
    "pickup": "CIKARANG",
    "tujuan": "CKR - JATIM TENTATIVE",
    "type_truck": "CDDL",
    "driver": "JATMIYANTA",
    "no_plat": "F 9648 TH",
    "kontak_driver": "082118558105",
    "status_unit": "ASSIGNED",
}])

audit_wrong = _compute_ml_observability(test_msg_2b, 1, model_2b_wrong)
sf_wrong = audit_wrong.get("slot_fields", {})
print(f"  tgl_muat TP={sf_wrong['tgl_muat']['tp']}  FP={sf_wrong['tgl_muat']['fp']}  FN={sf_wrong['tgl_muat']['fn']}")
assert sf_wrong["tgl_muat"]["tp"] == 0, f"Wrong date should have 0 TP, got {sf_wrong['tgl_muat']['tp']}"
assert sf_wrong["tgl_muat"]["fp"] == 1, f"Wrong date should have 1 FP, got {sf_wrong['tgl_muat']['fp']}"
assert sf_wrong["tgl_muat"]["fn"] == 1, f"Wrong date should have 1 FN, got {sf_wrong['tgl_muat']['fn']}"
print("  >> Model error correctly detected as FP+FN!")


# ─── TEST 7: Tolerant date format matching ───
print("\n=== TEST 7: Tolerant Date Format Matching ===")
# GT outputs "12 MARET 2026" but model outputs "12 Maret 2026" (different casing)
test_msg_tol = (
    "[08.06, 10/3/2026] Akbar Rafay: Request Unit On Call Tgl 12 MARET 2026\n\n"
    "1 UNIT TWB 50 CBM\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : SEGERA\n"
    "Rute/tujuan : CGK - DPS\n"
    "driver  : BUDI\n"
    "Nopol  : B 1234 XY\n"
    "No hp  : 081234567890\n"
)

model_tol = pd.DataFrame([{
    "tgl_ro": "12 Maret 2026",         # different casing
    "tgl_muat": "12-03-2026",           # numeric format
    "pickup": "ARGOPANTES",
    "tujuan": "CGK - DPS",
    "type_truck": "TWB",
    "driver": "BUDI",
    "no_plat": "B 1234 XY",
    "kontak_driver": "081234567890",
    "status_unit": "ASSIGNED",
}])

audit_tol = _compute_ml_observability(test_msg_tol, 1, model_tol)
sf_tol = audit_tol.get("slot_fields", {})
print(f"  tgl_ro   TP={sf_tol['tgl_ro']['tp']}  FP={sf_tol['tgl_ro']['fp']}  FN={sf_tol['tgl_ro']['fn']}")
print(f"  tgl_muat TP={sf_tol['tgl_muat']['tp']}  FP={sf_tol['tgl_muat']['fp']}  FN={sf_tol['tgl_muat']['fn']}")
assert sf_tol["tgl_ro"]["tp"] == 1, f"Tolerant tgl_ro should be TP"
assert sf_tol["tgl_muat"]["tp"] == 1, f"Tolerant tgl_muat (numeric format) should be TP"
print("  >> Tolerant date matching PASSED!")


print("\n" + "=" * 60)
print("ALL EVALUATOR TESTS PASSED!")
print("=" * 60)
