"""Full integration test: process the real test case file."""
import sys, json
sys.path.insert(0, ".")
from audit_dashboard import extract_ground_truth_entities, _split_wa_messages

# Read the real test case file
with open(r"tests\masive _test\refill test\real_lapangan_tc_combine_part2_mix\tc_day1_seed_real_part2_mix.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# Split into WA messages first (like the dashboard does)
messages = _split_wa_messages(raw_text)
print(f"Total WA messages: {len(messages)}\n")

total_assigned = 0
total_partial = 0
total_units = 0

for i, msg in enumerate(messages):
    entities = extract_ground_truth_entities(msg)
    if not entities:
        continue
    print(f"=== Message [{i+1}] ===")
    # Show first 80 chars of message
    preview = msg[:80].replace("\n", " ") + "..."
    print(f"  Preview: {preview}")
    print(f"  tgl_ro: {entities[0]['tgl_ro']}")
    print(f"  Units extracted: {len(entities)}")
    for j, e in enumerate(entities):
        status_icon = "✓" if e["status_unit"] == "ASSIGNED" else "○"
        driver_display = e["driver"] if e["driver"] else "(empty)"
        print(f"    [{j+1}] {status_icon} driver={driver_display:15s} tgl_muat={e['tgl_muat']:22s} "
              f"tujuan={e['tujuan']:25s} nopol={e['nopol']}")
        if e["status_unit"] == "ASSIGNED":
            total_assigned += 1
        else:
            total_partial += 1
        total_units += 1
    print()

print("=" * 60)
print(f"TOTAL UNITS: {total_units}")
print(f"  ASSIGNED: {total_assigned}")
print(f"  PARTIAL:  {total_partial}")
