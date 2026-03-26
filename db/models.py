import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Extraction(Base):
    __tablename__ = "extractions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id"), nullable=True)
    pickup = Column(String(255))
    tujuan = Column(String(255))
    vendor = Column(String(255))
    truck_type = Column(String(120))
    unit_count = Column(Integer)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number = Column(String(120), unique=True, index=True)
    tgl_ro = Column(String(60))
    tgl_muat = Column(String(60))
    vendor = Column(String(255), index=True)
    pickup = Column(String(255), index=True)
    tujuan = Column(String(255), index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class OrderUnit(Base):
    __tablename__ = "order_units"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    no_plat = Column(String(80))
    driver = Column(String(255))
    driver_contact = Column(String(80))
    spk_number = Column(String(120))
    sj_do_number = Column(String(120))
    status = Column(String(40), default="UNASSIGNED")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

