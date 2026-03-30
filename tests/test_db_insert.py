import sys
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.database import SessionLocal  # noqa: E402
from db.persistence import extract_month_year_from_tgl_muat, generate_chat_hash  # noqa: E402
from models.order_dataset import OrderDataset  # noqa: E402
from models.raw_chat import RawChat  # noqa: E402


def main() -> None:
    session = SessionLocal()
    try:
        sample_chat = f"REQUEST ORDER ONCALL 06 MARET 2026 | {uuid.uuid4()}"
        raw = RawChat(
            chat_hash=generate_chat_hash(sample_chat),
            chat_text=sample_chat,
        )
        session.add(raw)
        session.flush()

        tgl_muat = "05 FEBRUARI 2026"
        month_segment, year_segment = extract_month_year_from_tgl_muat(tgl_muat)

        order = OrderDataset(
            raw_chat_id=raw.id,
            job_number="001/JNE-RAFAY/II/2026",
            tgl_ro="06 MARET 2026",
            tgl_muat=tgl_muat,
            pickup="ARGOPANTES",
            tujuan="CGK, PKU",
            no_plat="BM 8486 AU",
            type_truck="TWB",
            driver="Syarial",
            kontak_driver="081317708658",
            status_unit="ASSIGNED",
            month_segment=month_segment,
            year_segment=year_segment,
        )
        session.add(order)
        session.commit()

        print("SUCCESS: sample RawChat and OrderDataset inserted")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
