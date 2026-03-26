import os
import logging
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[1] / ".env"
    loaded = load_dotenv(_env_path, override=True)
    if os.getenv("DB_DEBUG", "").lower() in ("1", "true", "yes", "on"):
        logger.info("Loaded .env from %s (found=%s)", _env_path, loaded)
except Exception:
    if os.getenv("DB_DEBUG", "").lower() in ("1", "true", "yes", "on"):
        logger.exception("Failed to load .env")

_engine = None
_SessionLocal = None

def _db_debug_enabled():
    return os.getenv("DB_DEBUG", "").lower() in ("1", "true", "yes", "on")

def _env_first(*keys):
    for key in keys:
        val = os.getenv(key)
        if val:
            return val
    return None

def get_database_url():
    url = _env_first("DATABASE_URL", "POSTGRES_URL", "POSTGRESQL_URL")
    if url:
        return url

    host = _env_first("PGHOST", "POSTGRES_HOST", "POSTGRESQL_HOST")
    database = _env_first("PGDATABASE", "POSTGRES_DB", "POSTGRESQL_DB")
    user = _env_first("PGUSER", "POSTGRES_USER", "POSTGRESQL_USER")
    password = _env_first("PGPASSWORD", "POSTGRES_PASSWORD", "POSTGRESQL_PASSWORD")
    port = _env_first("PGPORT", "POSTGRES_PORT", "POSTGRESQL_PORT")

    if not (host and database and user and password):
        if _db_debug_enabled():
            logger.warning("Missing PG env vars: host=%s db=%s user=%s password=%s port=%s", bool(host), bool(database), bool(user), bool(password), bool(port))
        return None

    port_part = f":{port}" if port else ""
    user_enc = quote_plus(user)
    pass_enc = quote_plus(password)
    return f"postgresql+psycopg2://{user_enc}:{pass_enc}@{host}{port_part}/{database}"

def db_enabled():
    return bool(get_database_url())

def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        if not url:
            if _db_debug_enabled():
                logger.warning("DB disabled: no database URL or PG env vars found")
            return None
        if _db_debug_enabled():
            logger.info("DB url loaded; creating engine")
        _engine = create_engine(url, pool_pre_ping=True, future=True)
    return _engine

def get_session():
    global _SessionLocal
    engine = get_engine()
    if engine is None:
        if _db_debug_enabled():
            logger.warning("DB session requested but engine is None")
        return None
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return _SessionLocal()

def init_db():
    engine = get_engine()
    if engine is None:
        return False
    try:
        Base.metadata.create_all(bind=engine)
        if _db_debug_enabled():
            logger.info("DB init complete")
        return True
    except Exception:
        if _db_debug_enabled():
            logger.exception("DB init failed")
        return False
