import re

text = "requestorderoncall04mei2026"
m = re.search(r'(?:oncall|tgl)[^\d]*([0-9]{1,2}[a-z]+(?:20)?26)', text)
if m:
    print(m.group(1))
