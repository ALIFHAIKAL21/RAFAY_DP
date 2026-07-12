import re

with open('stage2_pair_visual_test.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find extract_pencocokan or similar
matches = re.finditer(r'def\s+([A-Za-z0-9_]+)\s*\(.*?\)\s*(?:->.*?)?:', content)
for m in matches:
    print(m.group(1))

