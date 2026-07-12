import sys
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()
sys.modules['st_aggrid'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()

import stage2_pair_visual_test as test_module

events = test_module.extract_pencocokan()

false_negatives = []
for ev in events:
    gt_label = test_module.stage2_event_ground_truth(ev)
    pred_label = test_module.stage2_event_predicted_label(ev)
    
    if gt_label == "NO_MATCH" and pred_label == "MATCH":
        false_negatives.append(ev)

print(f"Total pairs where GT says NO_MATCH but Model says MATCH: {len(false_negatives)}")
for i, ev in enumerate(false_negatives[:10]):
    print(f"\n--- Pair {i+1} ---")
    print("ORDER INDUK:", ev['order_state_text'][:100].replace('\n', ' '))
    print("ORDER SUSULAN:", ev['incoming_text'][:100].replace('\n', ' '))
    print("PREDICTION:", pred_label)
    print("GT LABEL:", gt_label)

