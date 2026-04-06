"""
Audit log model – immutable record of all business actions.
"""
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base
from app.models.base import generate_uuid
from datetime import datetime, timezone


class AuditLog(Base):
    """Immutable audit trail entry."""
    __tablename__ = 'audit_logs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        nullable=False, index=True,
    )
    user_id = Column(String(36), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(String(36), nullable=True)
    description = Column(Text, nullable=True)
    before_value = Column(Text, nullable=True)  # JSON snapshot
    after_value = Column(Text, nullable=True)   # JSON snapshot
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    module = Column(String(50), nullable=True)


class MasterDataChangeLog(Base):
    """Change log for master data versioning (FG codes, blends, calibrations)."""
    __tablename__ = 'master_data_change_log'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(36), nullable=True)
    change_reason = Column(Text, nullable=True)
