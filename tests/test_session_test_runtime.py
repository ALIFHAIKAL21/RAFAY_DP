from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from session_test_runtime import resolve_session_test_database  # noqa: E402


def clear_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "IDP_SESSION_TEST_ADMIN_URL",
        "IDP_SESSION_TEST_ADMIN_DB",
        "IDP_SESSION_TEST_DB_NAME",
        "DATABASE_URL",
        "DB_NAME",
        "PGDATABASE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_session_test_database_is_derived_from_source_connection(monkeypatch):
    clear_test_env(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:secret@localhost:5432/logistic_parser",
    )
    monkeypatch.setenv(
        "IDP_SESSION_TEST_DB_NAME",
        "logistic_parser_session_test",
    )

    config = resolve_session_test_database()

    assert config.source_url.database == "logistic_parser"
    assert config.admin_url.database == "postgres"
    assert config.target_url.database == "logistic_parser_session_test"


@pytest.mark.parametrize(
    "unsafe_name",
    [
        "logistic_parser",
        "postgres",
        "session_test",
        "logistic-parser-session-test",
        "logistic_parser_test",
    ],
)
def test_session_test_database_rejects_unsafe_names(monkeypatch, unsafe_name):
    clear_test_env(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:secret@localhost:5432/logistic_parser",
    )
    monkeypatch.setenv("IDP_SESSION_TEST_DB_NAME", unsafe_name)

    with pytest.raises(RuntimeError):
        resolve_session_test_database()

