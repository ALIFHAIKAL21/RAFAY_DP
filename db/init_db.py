import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.session import init_db  # noqa: E402


def main() -> None:
    ok = init_db()
    if not ok:
        raise RuntimeError("DB init gagal")
    print("SUCCESS: tables created/updated (raw_chats, order_dataset)")


if __name__ == "__main__":
    main()
