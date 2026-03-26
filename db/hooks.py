from sqlalchemy.exc import SQLAlchemyError
from .models import WhatsAppMessage, Extraction, Order, OrderUnit
from .session import db_enabled, get_session


def _safe_text(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def save_raw_chat(raw_text):
    if not db_enabled():
        return None
    session = get_session()
    if session is None:
        return None
    try:
        msg = WhatsAppMessage(raw_text=str(raw_text))
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg.id
    except SQLAlchemyError:
        session.rollback()
        return None
    finally:
        session.close()


def save_extractions_from_df(df, message_id=None):
    if not db_enabled():
        return 0
    session = get_session()
    if session is None:
        return 0
    count = 0
    try:
        for _, row in df.iterrows():
            extraction = Extraction(
                message_id=message_id,
                pickup=_safe_text(row.get('ORIGIN')),
                tujuan=_safe_text(row.get('DESTINATION')),
                vendor=_safe_text(row.get('VENDOR')),
                truck_type=_safe_text(row.get('UNIT_TYPE')),
                unit_count=row.get('UNIT_COUNT') if 'UNIT_COUNT' in row else None,
            )
            session.add(extraction)
            count += 1
        session.commit()
        return count
    except SQLAlchemyError:
        session.rollback()
        return 0
    finally:
        session.close()


def save_orders_from_df(df):
    if not db_enabled():
        return 0
    session = get_session()
    if session is None:
        return 0
    count = 0
    try:
        for _, row in df.iterrows():
            job_number = _safe_text(row.get('Job Number'))
            if job_number:
                existing = session.query(Order).filter_by(job_number=job_number).first()
                if existing:
                    continue
            order = Order(
                job_number=job_number,
                tgl_ro=_safe_text(row.get('Tgl RO')),
                tgl_muat=_safe_text(row.get('Tgl Muat')),
                vendor=_safe_text(row.get('Vendor')),
                pickup=_safe_text(row.get('Pickup')),
                tujuan=_safe_text(row.get('Tujuan')),
            )
            session.add(order)
            session.flush()
            unit = OrderUnit(
                order_id=order.id,
                no_plat=_safe_text(row.get('No. Plat')),
                driver=_safe_text(row.get('Driver')),
                driver_contact=_safe_text(row.get('Kontak Driver')),
                spk_number=None,
                sj_do_number=None,
            )
            session.add(unit)
            count += 1
        session.commit()
        return count
    except SQLAlchemyError:
        session.rollback()
        return 0
    finally:
        session.close()
