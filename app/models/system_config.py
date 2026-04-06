"""
System configuration model – stores admin-configurable settings.
Maps to legacy: Application settings / system preferences
"""
from sqlalchemy import Column, String, Text, Boolean
from app.database import Base
from app.models.base import AuditMixin, generate_uuid


class SystemConfig(Base, AuditMixin):
    __tablename__ = 'system_config'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    is_sensitive = Column(Boolean, default=False)  # mask in UI
    category = Column(String(50), nullable=True)   # grouping: auth, report, batch, etc.
