from __future__ import annotations

import os
import re
import socket
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DB_NAME = "logistic_parser_session_test"
PROTECTED_DATABASE_NAMES = {
    "logistic_parser",
    "postgres",
    "template0",
    "template1",
}


@dataclass(frozen=True)
class SessionTestDatabase:
    source_url: URL
    admin_url: URL
    target_url: URL
    database_name: str


def load_session_test_environment() -> None:
    explicit_environment = set(os.environ)
    load_dotenv(ROOT_DIR / ".env", override=False)
    for name, value in dotenv_values(ROOT_DIR / ".env.session_test").items():
        if name not in explicit_environment and value is not None:
            os.environ[name] = value


def _env(*names: str, default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _base_database_url() -> URL:
    explicit_admin_url = str(
        os.getenv("IDP_SESSION_TEST_ADMIN_URL", "") or ""
    ).strip()
    if explicit_admin_url:
        return make_url(explicit_admin_url)

    explicit_database_url = str(os.getenv("DATABASE_URL", "") or "").strip()
    if explicit_database_url:
        return make_url(explicit_database_url)

    host = _env("DB_HOST", "PGHOST", default="localhost")
    port = int(_env("DB_PORT", "PGPORT", default="5432"))
    user = _env("DB_USER", "PGUSER", default="postgres")
    password = _env("DB_PASSWORD", "PGPASSWORD", default="NewStrongPassword")
    database = _env("DB_NAME", "PGDATABASE", default="logistic_parser")
    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def resolve_session_test_database() -> SessionTestDatabase:
    load_session_test_environment()
    base_url = _base_database_url()
    database_name = str(
        os.getenv("IDP_SESSION_TEST_DB_NAME", DEFAULT_TEST_DB_NAME) or ""
    ).strip()

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*_session_test", database_name):
        raise RuntimeError(
            "Nama DB test wajib berupa identifier PostgreSQL yang berakhiran "
            f"'_session_test', actual={database_name!r}."
        )

    base_database = str(base_url.database or "").strip()
    protected_names = set(PROTECTED_DATABASE_NAMES)
    if base_database and not base_database.endswith("_session_test"):
        protected_names.add(base_database)
    if database_name in protected_names:
        raise RuntimeError(f"Nama DB test dilindungi dan tidak boleh dipakai: {database_name}")

    admin_database = str(
        os.getenv("IDP_SESSION_TEST_ADMIN_DB", "postgres") or "postgres"
    ).strip()
    admin_url = base_url.set(database=admin_database)
    target_url = base_url.set(database=database_name)
    if target_url == admin_url:
        raise RuntimeError("DB target test tidak boleh sama dengan DB administrasi.")

    return SessionTestDatabase(
        source_url=base_url,
        admin_url=admin_url,
        target_url=target_url,
        database_name=database_name,
    )


def ensure_session_test_database(config: SessionTestDatabase) -> bool:
    admin_engine = create_engine(
        config.admin_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        future=True,
    )
    created = False
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": config.database_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{config.database_name}"'))
                created = True
    finally:
        admin_engine.dispose()

    target_engine = create_engine(config.target_url, pool_pre_ping=True, future=True)
    try:
        with target_engine.connect() as conn:
            current_database = conn.execute(text("SELECT current_database()")).scalar_one()
        if current_database != config.database_name:
            raise RuntimeError(
                "Verifikasi DB test gagal: "
                f"expected={config.database_name!r}, actual={current_database!r}."
            )
    finally:
        target_engine.dispose()
    return created


def port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def masked_url(url: URL) -> str:
    return url.render_as_string(hide_password=True)
