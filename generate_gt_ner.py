import json
import re

qty_list = []
ro_date_list = []
load_date_list = []
origin_list = []
destination_list = []
plate_list = []
unit_type_list = []
driver_list = []
phone_list = []

with open('data_uji_demo/data_uji_demo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
        
    # RO_DATE
    m = re.search(r'(?i)ONCALL\s+(.*?):?$', stripped)
    if m:
        ro_date_list.append(m.group(1).strip())
        continue
    m = re.search(r'(?i)Tgl\s+(.*?):?$', stripped)
    if m:
        ro_date_list.append(m.group(1).strip())
        continue
        
    # QTY & TYPE
    m = re.match(r'(?i)^(\d+)\s+UNIT\s+(.*)$', stripped)
    if m:
        qty_list.append(m.group(1).strip())
        unit_type_list.append(m.group(2).strip())
        continue
        
    # ORIGIN
    m = re.match(r'(?i)^(Lokasi|LOKASI|Loksi|LKASI PICKUP|Lokasi Loading)\s*[:]?\s*(.+)$', stripped)
    if m:
        origin_list.append(m.group(2).strip())
        continue
        
    # LOAD DATE
    m = re.match(r'(?i)^(Waktu loading|Waktu loding|Waktu load|Wkt load|loading|Waktu|lOADING)\s*[:]?\s*(.+)$', stripped)
    if m:
        val = m.group(2).strip()
        if val:
            load_date_list.append(val)
        continue
        
    # DESTINATION
    m = re.match(r'(?i)^(Tujuan|Rute/ tuj|Rute / Tujuan|Rute/tujan|Rute/tujuan|Rute)\s*[:]?\s*(.+)$', stripped)
    if m:
        val = m.group(2).strip()
        if val:
            destination_list.append(val)
        continue
        
    # DRIVER
    m = re.match(r'(?i)^(Nama Sopir|DRIVER|Drver|Drivr|Sopir|Supir|DRVR|NAMA|Nama)\s*[:]?\s*(.*)$', stripped)
    if m:
        val = m.group(2).strip()
        if val.startswith(':'): val = val[1:].strip()
        if val:
            driver_list.append(val)
        continue
        
    # PLATE
    m = re.match(r'(?i)^(No Kendaraan|Nopolisi|Nopoll|NO POL|No pol|NOPOL|Plat|Nopol)\s*[:]?\s*(.*)$', stripped)
    if m:
        val = m.group(2).strip()
        if val.startswith(':'): val = val[1:].strip()
        if val:
            plate_list.append(val)
        continue
        
    # PHONE
    m = re.match(r'(?i)^(No Telepon|No hpp|NO HP|No hp|Kontak|HP|Hp|p)\s*[:]?\s*(.*)$', stripped)
    if m:
        val = m.group(2).strip()
        if val.startswith(':'): val = val[1:].strip()
        if val:
            phone_list.append(val)
        continue

gt_data = {
    "data_uji_demo.txt": {
        "UNIT_QTY": qty_list,
        "RO_DATE": ro_date_list,
        "LOAD_DATE": load_date_list,
        "ORIGIN": origin_list,
        "DESTINATION": destination_list,
        "PLATE": plate_list,
        "UNIT_TYPE": unit_type_list,
        "DRIVER": driver_list,
        "PHONE": phone_list
    }
}

with open('data_uji_demo/gt_ner.json', 'w', encoding='utf-8') as f:
    json.dump(gt_data, f, indent=4)

print("Generated gt_ner.json with", len(qty_list), "orders and multiple attributes.")
