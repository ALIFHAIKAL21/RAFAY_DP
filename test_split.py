import sys
import re
from stage2_pair_visual_test import split_new_order_messages

with open('data_uji/positife_combine copy.txt', 'r', encoding='utf-8') as f:
    text = f.read()

chunks = split_new_order_messages(text)
print(f'Found {len(chunks)} chunks.')
for i, chunk in enumerate(chunks[:5]):
    print(f'Chunk {i}: {chunk[:50].replace(chr(10), " ")}')
