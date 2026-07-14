import re
import random

with open('data_uji_demo/data_uji_demo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def get_variation(date_str):
    # The 3 new variations
    # Var 1: [time, date] Akbar Rafay: Request Unit On Call Tgl {date}
    # Var 2: Akbar Rafay: REQUEST ORDER ONCALL {date}
    # Var 3: REQUER ORDER ONCALL {date}
    # Original: REQUEST ORDER ONCALL {date}:
    
    variations = [
        f"[08.15, 12/4/2026] Akbar Rafay: Request Unit On Call Tgl {date_str}",
        f"Akbar Rafay: REQUEST ORDER ONCALL {date_str}",
        f"REQUER ORDER ONCALL {date_str}",
        f"REQEST ORDER ONCALL {date_str}:",
        f"REQUESTT ORDER ONCALL {date_str}"
    ]
    return random.choice(variations)

new_lines = []
for line in lines:
    m = re.match(r'(?i)^request\s+order\s+oncall\s+(.*?):?\s*$', line.strip())
    if m:
        date_str = m.group(1)
        new_header = get_variation(date_str)
        new_lines.append(new_header + "\n")
    else:
        new_lines.append(line)

with open('data_uji_demo/data_uji_demo.txt', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Done replacing headers.")
