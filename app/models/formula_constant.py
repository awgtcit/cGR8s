"""
Global formula constants for target weight calculation.
Stores Alpha, Beta, Delta, Dust_Moisture, Max_VF, Min_PD, Max_PD, NCG etc.
"""
from sqlalchemy import Column, String, Float, Boolean
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid


class FormulaConstant(Base, AuditMixin, VersionMixin):
    """Global constants used in the target weight engineering formulas."""
    __tablename__ = 'formula_constants'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Float, nullable=False)
    description = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
