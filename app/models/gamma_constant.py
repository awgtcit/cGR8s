"""
Gamma constant lookup table.
Gamma depends on Format, Plug Length, and a condition (N_tgt < 0.3).
"""
from sqlalchemy import Column, String, Float, Integer, Boolean
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid


class GammaConstant(Base, AuditMixin, VersionMixin):
    """Gamma lookup – value depends on format, plug_length, and condition."""
    __tablename__ = 'gamma_constants'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    format = Column(String(50), nullable=False, index=True)
    plug_length = Column(Integer, nullable=False)
    condition = Column(Boolean, nullable=False)  # True when N_tgt < 0.3
    selection_criteria = Column(String(100), nullable=True)
    value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
