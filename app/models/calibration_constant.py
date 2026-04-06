"""
Calibration constants model.
Stores calibration / model coefficients for each FG Code.
"""
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid


class CalibrationConstant(Base, AuditMixin, VersionMixin):
    """Calibration constants for target weight calculations."""
    __tablename__ = 'calibration_constants'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code_id = Column(String(36), ForeignKey('fg_codes.id'), nullable=False, index=True)
    fg_code_rel = relationship('FGCode', foreign_keys=[fg_code_id], lazy='joined')
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    n_tgt = Column(Float, nullable=True)  # Target Nicotine
