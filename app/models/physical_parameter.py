"""
Physical parameters model.
Stores physical measurement parameters for each FG Code / SKU.
"""
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid


class PhysicalParameter(Base, AuditMixin, VersionMixin):
    """Physical parameters linked to an FG Code."""
    __tablename__ = 'physical_parameters'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code_id = Column(String(36), ForeignKey('fg_codes.id'), nullable=False, index=True)
    fg_code_rel = relationship('FGCode', foreign_keys=[fg_code_id], lazy='joined')
    p_cu = Column(Float, nullable=True)        # Cigarette Paper CU
    t_vnt = Column(Float, nullable=True)       # Tip Ventilation
    f_pd = Column(Float, nullable=True)        # Filter Pressure Drop
    m_ip = Column(Float, nullable=True)        # Input Moisture
    cig_length = Column(Float, nullable=True)
    tobacco_rod_length = Column(Float, nullable=True)
    filter_length = Column(Float, nullable=True)
    plug_length = Column(Float, nullable=True)
    c_plg = Column(Float, nullable=True)       # Number of cuts
