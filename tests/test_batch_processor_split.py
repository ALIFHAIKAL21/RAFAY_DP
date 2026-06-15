from src.inference.batch_processor import ChatBatchProcessor


def test_smart_split_handles_request_header_typos_without_model_load():
    processor = ChatBatchProcessor.__new__(ChatBatchProcessor)
    raw_text = """[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 09 MARET 2026:
1 unit TWB 50 CBM
Lokasi : CIKOKOL

[05.31, 7/3/2026] Akbar Rafay: REQEST ORDER ONCALL 12 MARET 2026:
1 unit TWB 50 CBM
Lokasi : CIKOKOL

[05.31, 7/3/2026] Akbar Rafay: REQUESTT ORDER ONCALL 21 MARET 2026:
1 unit TWB 50 CBM
Lokasi : CIKOKOL

[05.31, 7/3/2026] Akbar Rafay: REQUES ORDER ONCALL 24 MARET 2026:
1 unit CDDL 24 CBM
Lokasi : MEGAHUB
"""

    chunks = processor.smart_split(raw_text)

    assert len(chunks) == 4
    assert "09 MARET 2026" in chunks[0]
    assert "12 MARET 2026" in chunks[1]
    assert "21 MARET 2026" in chunks[2]
    assert "24 MARET 2026" in chunks[3]
