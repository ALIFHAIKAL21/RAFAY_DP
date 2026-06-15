from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from session_test_runtime import resolve_session_test_database  # noqa: E402


ISOLATION_PROBE = r"""
import io
import zipfile

from db.persistence import (
    load_all_order_rows,
    load_all_raw_chat_records,
    load_stage2_match_audits,
    prepare_chat_for_parsing,
    reset_all_data,
    save_parsed_rows,
    save_stage2_match_audits,
)
from db.session_workspace import (
    archive_extraction_session,
    create_extraction_session,
    delete_extraction_session,
    export_active_session_bundle,
    refresh_active_session_auto_name,
    restore_extraction_session,
    set_active_extraction_session,
)

row_a = {
    "tgl_ro": "06 FEBRUARI 2026",
    "tgl_muat": "07 FEBRUARI 2026",
    "pickup": "CIKARANG",
    "tujuan": "SUB",
    "no_plat": "B 100 AA",
    "type_truck": "TWB 50 CBM",
    "driver": "ASEP",
    "kontak_driver": "081111111111",
    "status_unit": "ASSIGNED",
}
row_b = dict(
    row_a,
    no_plat="B 200 BB",
    driver="BUDI",
    kontak_driver="082222222222",
)
row_a_later = dict(
    row_a,
    tgl_ro="08 FEBRUARI 2026",
    no_plat="B 300 CC",
    driver="CANDRA",
    kontak_driver="083333333333",
)

session_a = create_extraction_session("")
session_b = None
try:
    should_parse_a, chat_a = prepare_chat_for_parsing("CHAT IDENTIK ANTAR SESI")
    assert should_parse_a is True
    assert save_parsed_rows(chat_a, [row_a, row_a_later]) == 2
    renamed = refresh_active_session_auto_name()
    assert renamed["name"] == "Order 06-08 Februari 2026"
    assert len(load_all_order_rows()) == 2
    assert len(load_all_raw_chat_records()) == 1
    assert save_stage2_match_audits(
        chat_a,
        [
            {
                "candidate_key": "session-a-candidate",
                "predicted_label": "MATCH",
                "p_match": 0.99,
                "confidence": 0.99,
                "decision_status": "SIAP_ISI_SLOT",
            }
        ],
    ) == 1
    assert len(load_stage2_match_audits(20)) == 1

    backup = export_active_session_bundle()
    assert backup
    with zipfile.ZipFile(io.BytesIO(backup)) as archive:
        names = archive.namelist()
        assert any(name.endswith("/orders.csv") for name in names)
        assert any(name.endswith("/raw_chats.json") for name in names)
        assert any(name.endswith("/stage2_audits.json") for name in names)

    session_b = create_extraction_session("Sesi B Manual")
    should_parse_b, chat_b = prepare_chat_for_parsing("CHAT IDENTIK ANTAR SESI")
    assert should_parse_b is True
    assert save_parsed_rows(chat_b, [row_b]) == 1
    assert load_all_order_rows()[0]["driver"] == "BUDI"
    assert load_stage2_match_audits(20) == []

    archive_extraction_session(session_b["id"])
    restore_extraction_session(session_b["id"])
    set_active_extraction_session(session_b["id"])

    set_active_extraction_session(session_a["id"])
    assert {row["driver"] for row in load_all_order_rows()} == {"ASEP", "CANDRA"}
    reset_all_data()
    assert load_all_order_rows() == []
    assert load_stage2_match_audits(20) == []

    set_active_extraction_session(session_b["id"])
    rows_b = load_all_order_rows()
    assert len(rows_b) == 1
    assert rows_b[0]["driver"] == "BUDI"
    assert load_stage2_match_audits(20) == []
finally:
    if session_b:
        delete_extraction_session(session_b["id"])
    delete_extraction_session(session_a["id"])
"""


def test_workspace_sessions_are_isolated_end_to_end():
    config = resolve_session_test_database()
    env = os.environ.copy()
    env["DATABASE_URL"] = config.target_url.render_as_string(hide_password=False)
    env["IDP_SESSION_TEST_MODE"] = "1"
    env["IDP_SESSION_TEST_DB_NAME"] = config.database_name

    completed = subprocess.run(
        [sys.executable, "-c", ISOLATION_PROBE],
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, (
        f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
    )
