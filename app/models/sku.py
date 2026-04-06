"""
SKU (Stock Keeping Unit) master model.
Maps to legacy: SKU reference data from Data sheet.
"""
from sqlalchemy import Column, String, Float, Boolean
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class SKU(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """SKU master data – product identification and nicotine/ventilation specs."""
    __tablename__ = 'skus'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sku_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(300), nullable=True)
    nicotine = Column(Float, nullable=True)
    ventilation = Column(Float, nullable=True)
    pd_code = Column(String(50), nullable=True)
    cig_code = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
