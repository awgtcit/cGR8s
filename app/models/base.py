"""
Base model mixin with common audit columns and soft-delete support.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER


class AuditMixin:
    """Adds created/updated audit trail columns to any model."""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String(36), nullable=True)  # User UUID from Auth-App
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_by = Column(String(36), nullable=True)


class SoftDeleteMixin:
    """Adds soft-delete flag to models."""

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(36), nullable=True)


class VersionMixin:
    """Optimistic concurrency control via row version counter."""

    row_version = Column(Integer, default=1, nullable=False)


def generate_uuid():
    """Generate a new UUID string for primary keys."""
    return str(uuid.uuid4())
