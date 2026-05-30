"""Debug: inspect exactly what the section splitter produces."""
import sys, re
sys.path.insert(0, ".")

raw = (
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

# Show how the section is split
unit_sections = re.split(
    r"(?i)(?=(?:^|\n)\s*waktu\s*loading\s*:)",
    raw,
)
for i, s in enumerate(unit_sections):
    print(f"--- Section [{i}] ---")
    print(repr(s))
    print()

# Now test the driver regex directly on the relevant section
section = unit_sections[-1].strip() if unit_sections else raw.strip()
print("=== Testing driver regex on section ===")
print(repr(section))
print()

# Test with the fixed pattern
m = re.search(r"^\s*(?:driver|nama\s*driver)\s*:\s*([^\r\n]*)", section, re.IGNORECASE | re.MULTILINE)
if m:
    print(f"Match found: group(0)={repr(m.group(0))}")
    print(f"             group(1)={repr(m.group(1))}")
    print(f"             stripped={repr(m.group(1).strip())}")
else:
    print("No match found")
