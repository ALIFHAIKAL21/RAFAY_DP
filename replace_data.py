import re

def load_list(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and line.strip() != 'pickup :|']
    return lines

nopols = load_list('nopol.txt')
drivers = load_list('driver.txt')
kontak = load_list('kontak_driver.txt')
pickups = load_list('pickup.txt')

nopol_idx = 0
driver_idx = 0
kontak_idx = 0
pickup_idx = 0

with open('data_uji_demo/data_uji_demo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
in_generated_section = False

for i, line in enumerate(lines):
    if line.startswith('REQUEST ORDER ONCALL 06 APR 2026:'):
        in_generated_section = True
    
    if not in_generated_section:
        output.append(line)
        continue
    
    # Process the line
    stripped = line.strip()
    
    # Lokasi / Pickup
    # Example: Loksi : SENTUL
    m_loc = re.match(r'^(Lokasi|LOKASI|Loksi|LKASI PICKUP|Lokasi Loading)\s*:\s*(.+)$', stripped)
    if m_loc:
        if pickup_idx < len(pickups):
            output.append(f"{m_loc.group(1)} : {pickups[pickup_idx]}\n")
            pickup_idx += 1
        else:
            output.append(line)
        continue
        
    # Driver
    m_drv = re.match(r'^(Driver|DRIVER|DRVR|NAMA|Drver|Supir|Drivr|Nama Sopir)\s*:\s*(.*)$', stripped)
    if m_drv:
        val = m_drv.group(2).strip()
        if val != '':
            if driver_idx < len(drivers):
                output.append(f"{m_drv.group(1)} : {drivers[driver_idx]}\n")
                driver_idx += 1
            else:
                output.append(line)
        else:
            output.append(line)
        continue
        
    # Nopol
    m_nopol = re.match(r'^(Nopol|NO POL|No pol|Nopoll|Plat|No Kendaraan|Nopolisi)\s*:\s*(.*)$', stripped)
    if m_nopol:
        val = m_nopol.group(2).strip()
        if val != '':
            if nopol_idx < len(nopols):
                output.append(f"{m_nopol.group(1)} : {nopols[nopol_idx]}\n")
                nopol_idx += 1
            else:
                output.append(line)
        else:
            output.append(line)
        continue
        
    # Kontak
    m_hp = re.match(r'^(No hp|NO HP|HP|No hpp|No Telepon|Kontak|Hp)\s*:\s*(.*)$', stripped)
    if m_hp:
        val = m_hp.group(2).strip()
        if val != '':
            if kontak_idx < len(kontak):
                # Clean up kontak driver value, remove leading pipe if any
                clean_kontak = kontak[kontak_idx].lstrip('|').strip()
                output.append(f"{m_hp.group(1)} : {clean_kontak}\n")
                kontak_idx += 1
            else:
                output.append(line)
        else:
            output.append(line)
        continue
        
    output.append(line)

with open('data_uji_demo/data_uji_demo.txt', 'w', encoding='utf-8') as f:
    f.writelines(output)
print(f"Replaced {driver_idx} drivers, {nopol_idx} nopols, {kontak_idx} kontak, {pickup_idx} pickups.")
