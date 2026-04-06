"""
Machine master model.
Maps to legacy: Machine reference data from Data sheet.
"""
from sqlalchemy import Column, String, Boolean
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class Machine(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """Machine master data – one row per production machine."""
    __tablename__ = 'machines'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    machine_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    plant = Column(String(50), nullable=True)
    format_type = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
