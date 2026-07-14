import re

with open('data_uji_demo/data_uji_demo.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

unique_qtys = list(range(7, 25))
qty_idx = 0

with open('data_uji_demo/data_uji_demo.txt', 'w', encoding='utf-8') as f:
    for line in lines:
        m = re.match(r'(?i)^(\d+)\s+(UNIT\s+.*)$', line.strip())
        if m and qty_idx < len(unique_qtys):
            # Replace the number
            new_line = str(unique_qtys[qty_idx]) + " " + m.group(2) + "\n"
            f.write(new_line)
            qty_idx += 1
        else:
            f.write(line)

print("Updated data_uji_demo.txt with unique quantities.")
