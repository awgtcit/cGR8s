"""
Blend master model.
Maps to legacy: Blend reference data in GTIN / master reference sheet
"""
from sqlalchemy import Column, String, Float, Boolean
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class BlendMaster(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """Blend composition master data."""
    __tablename__ = 'blend_master'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    blend_code = Column(String(50), unique=True, nullable=False, index=True)
    blend_name = Column(String(100), nullable=False)
    blend_gtin = Column(String(50), nullable=True)
    n_bld = Column(Float, nullable=True)  # Blend Nicotine content
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
