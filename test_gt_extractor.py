"""Quick test: validate extract_ground_truth_entities fixes BUG 1 & BUG 2."""
import sys, json
sys.path.insert(0, ".")
from audit_dashboard import extract_ground_truth_entities

# ── BUG 1: Spill-over (empty driver must NOT capture next label) ──
test1 = (
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
r1 = extract_ground_truth_entities(test1)
print("=== BUG 1: Empty driver spill-over ===")
for e in r1:
    print(f"  driver=[{e['driver']}]  nopol=[{e['nopol']}]  status=[{e['status_unit']}]")
assert r1[0]["driver"] == "", f"BUG1 FAIL: driver should be empty, got [{r1[0]['driver']}]"
assert r1[0]["status_unit"] == "PARTIAL", "BUG1 FAIL: status should be PARTIAL"
print("  >> BUG 1 FIXED!\n")

# ── BUG 2A: Time only → tgl_muat = tgl_ro ──
test2a = (
    "[08.06, 10/3/2026] Akbar Rafay: Request Unit On Call Tgl 12 MARET 2026\n\n"
    "3 UNIT TWB 50 CBM\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : 21:00\n"
    "Rute/tujuan : CGK - DPS\n"
    "driver  : M SYAICHONI\n"
    "Nopol  : N 8872 RK\n"
    "No hp  : 081231895971\n"
)
r2a = extract_ground_truth_entities(test2a)
print("=== BUG 2A: Time only -> tgl_ro ===")
print(f"  tgl_ro=[{r2a[0]['tgl_ro']}]  tgl_muat=[{r2a[0]['tgl_muat']}]")
assert r2a[0]["tgl_muat"] == "12 MARET 2026", f"FAIL: got [{r2a[0]['tgl_muat']}]"
print("  >> KONDISI A FIXED!\n")

# ── BUG 2B: Time + explicit date → parse the date ──
test2b = (
    "[08.05, 10/3/2026] Akbar Rafay: Request Unit On Call Tgl 12 MARET 2026\n\n"
    "3 UNIT CDDL 24 CBM\n"
    "Lokasi : CIKARANG\n"
    "Waktu loading : 06:00/13-03-26\n"
    "Rute/tujuan : CKR - JATIM TENTATIVE\n"
    "driver  : JATMIYANTA\n"
    "Nopol  : F 9648 TH\n"
    "No hp  : 082118558105\n"
)
r2b = extract_ground_truth_entities(test2b)
print("=== BUG 2B: Time + date -> explicit date ===")
print(f"  tgl_ro=[{r2b[0]['tgl_ro']}]  tgl_muat=[{r2b[0]['tgl_muat']}]")
assert r2b[0]["tgl_muat"] == "13 MARET 2026", f"FAIL: got [{r2b[0]['tgl_muat']}]"
print("  >> KONDISI B FIXED!\n")

# ── BUG 2C: SEGERA → tgl_muat = tgl_ro ──
test2c = (
    "[05.34, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 12 FEBRUARI 2026:\n\n"
    "3 UNIT TWB 50 Cbm\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : SEGERA\n"
    "Rute/tujuan : CGK - SUB\n"
    "driver  : Rosyit\n"
    "Nopol  : B 9563 TEU\n"
    "No hp  : 082313572678\n"
)
r2c = extract_ground_truth_entities(test2c)
print("=== BUG 2C: SEGERA -> tgl_ro ===")
print(f"  tgl_ro=[{r2c[0]['tgl_ro']}]  tgl_muat=[{r2c[0]['tgl_muat']}]")
assert r2c[0]["tgl_muat"] == "12 FEBRUARI 2026", f"FAIL: got [{r2c[0]['tgl_muat']}]"
print("  >> KONDISI C FIXED!\n")

# ── Multi-unit test with mixed statuses ──
test_multi = (
    "[05.38, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 13 FEBRUARI 2026:\n\n"
    "5 UNIT TWB 50 Cbm\n"
    "Lokasi : ARGOPANTES\n"
    "Waktu loading : 15:00\n"
    "Rute/tujuan : CGK - PKU\n"
    "driver  : HERMAN\n"
    "Nopol  : B 9718 TJ\n"
    "No hp  : 087844510846\n\n"
    "Waktu loading : 02:00 14-02-2026\n"
    "Rute/tujuan : CGK - PKU\n"
    "driver  :\n"
    "Nopol  :\n"
    "No hp  :\n"
)
rm = extract_ground_truth_entities(test_multi)
print("=== MULTI-UNIT: 2 units (1 ASSIGNED, 1 PARTIAL w/ explicit date) ===")
for i, e in enumerate(rm):
    print(f"  [{i}] driver=[{e['driver']}] status=[{e['status_unit']}] "
          f"tgl_ro=[{e['tgl_ro']}] tgl_muat=[{e['tgl_muat']}] "
          f"tujuan=[{e['tujuan']}] pickup=[{e['pickup']}] type=[{e['type_truck']}]")
assert len(rm) == 2, f"Expected 2 units, got {len(rm)}"
assert rm[0]["driver"] == "HERMAN"
assert rm[0]["status_unit"] == "ASSIGNED"
assert rm[0]["tgl_muat"] == "13 FEBRUARI 2026"  # time only → tgl_ro
assert rm[1]["driver"] == ""
assert rm[1]["status_unit"] == "PARTIAL"
assert rm[1]["tgl_muat"] == "14 FEBRUARI 2026"  # explicit date
print("  >> MULTI-UNIT PASSED!\n")

print("=" * 50)
print("ALL TESTS PASSED")

# Pretty-print one full output for reference
print("\nSample output (JSON):")
print(json.dumps(rm, indent=2, ensure_ascii=False))
