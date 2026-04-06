"""
Tobacco Blend Analysis model.
Maps to legacy: Monthly blend nicotine/moisture time-series data from Data sheet.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class TobaccoBlendAnalysis(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """Monthly tobacco blend analysis – nicotine and moisture readings."""
    __tablename__ = 'tobacco_blend_analysis'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    period_year = Column(Integer, nullable=True)
    period_month = Column(Integer, nullable=True)
    blend_name = Column(String(100), nullable=False, index=True)
    nic_wet = Column(Float, nullable=True)
    nic_dry = Column(Float, nullable=True)
    dispatch_moisture = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
