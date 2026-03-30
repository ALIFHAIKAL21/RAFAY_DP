import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Load .env from project root if available.
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)


def _env(*names: str, default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


DB_HOST = _env("DB_HOST", "PGHOST", default="localhost")
DB_PORT = _env("DB_PORT", "PGPORT", default="5432")
DB_NAME = _env("DB_NAME", "PGDATABASE", default="logistic_parser")
DB_USER = _env("DB_USER", "PGUSER", default="postgres")
DB_PASSWORD = _env("DB_PASSWORD", "PGPASSWORD", default="NewStrongPassword")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
