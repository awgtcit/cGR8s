"""
Lookup / reference table model.
"""
from sqlalchemy import Column, String, Integer, Boolean
from app.database import Base
from app.models.base import AuditMixin, generate_uuid


class Lookup(Base, AuditMixin):
    """Generic lookup table for dropdowns and reference values."""
    __tablename__ = 'lookups'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(50), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_id = Column(String(36), nullable=True)  # for hierarchical lookups
