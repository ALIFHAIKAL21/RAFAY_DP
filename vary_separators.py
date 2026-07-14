import re
import random

with open('data_uji_demo/data_uji_demo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_generated_section = False

def modify_separator(attr, value):
    # Variations based on data_mentah.txt
    # 1. "Attr : Value"
    # 2. "Attr: Value"
    # 3. "Attr:Value"
    # 4. "Attr  : Value"
    # 5. "Attr Value" (only if value is not empty to avoid confusion, although empty is fine)
    
    choice = random.randint(1, 6)
    if choice == 1:
        return f"{attr} : {value}"
    elif choice == 2:
        return f"{attr}: {value}"
    elif choice == 3:
        # If value is empty, just keep the colon
        return f"{attr}:{value}"
    elif choice == 4:
        return f"{attr}  : {value}"
    elif choice == 5:
        return f"{attr} :  {value}"
    elif choice == 6:
        # No colon! But only if value is not empty (if empty it just becomes attr)
        if value.strip() != "":
            return f"{attr} {value}"
        else:
            return f"{attr} :"

for line in lines:
    if line.startswith('REQUESTT ORDER ONCALL 06 APR 2026'):
        in_generated_section = True
        
    if not in_generated_section:
        new_lines.append(line)
        continue
        
    # Match any attribute line: Attr : Value
    m = re.match(r'^([^:]+?)\s*:\s*(.*)$', line)
    
    # Exceptions: do not touch lines like "REQUEST ORDER..." or empty lines
    if line.strip() == '' or line.strip().lower().startswith('request') or 'UNIT' in line or line.strip().lower().startswith('akbar') or line.strip().lower().startswith('requer') or line.strip().lower().startswith('[0'):
        new_lines.append(line)
        continue
        
    if m:
        attr = m.group(1).strip()
        val = m.group(2).strip()
        
        # Don't touch Lokasi if it's the main header unless it's a known attr
        known_attrs = ['waktu', 'loading', 'rute', 'tujuan', 'lokasi', 'loksi', 'lkasi', 'supir', 'driver', 'drvr', 'nama', 'drivr', 'drver', 'plat', 'no pol', 'nopol', 'no kendaraan', 'nopolisi', 'nopoll', 'hp', 'no hp', 'kontak', 'no hpp', 'no telepon']
        
        is_known = False
        for k in known_attrs:
            if k in attr.lower():
                is_known = True
                break
                
        if is_known:
            new_line = modify_separator(attr, val) + "\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('data_uji_demo/data_uji_demo.txt', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Done applying separator variations.")
