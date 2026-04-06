"""
Product version model – versioned master data for New Product Development.
Maps to legacy: (new) product lifecycle tracking
"""
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, DateTime
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class ProductVersion(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """Versioned product/SKU definition for new product development workflow."""
    __tablename__ = 'product_versions'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code_id = Column(String(36), ForeignKey('fg_codes.id'), nullable=True, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default='Draft', index=True)
    # Draft -> Review -> Approved -> Retired

    # Snapshot of product attributes at this version
    brand = Column(String(100), nullable=True)
    fg_gtin = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
    blend_code = Column(String(50), nullable=True)
    blend_name = Column(String(100), nullable=True)

    # Physical params snapshot
    cig_length = Column(Float, nullable=True)
    tobacco_rod_length = Column(Float, nullable=True)
    filter_length = Column(Float, nullable=True)
    plug_length = Column(Float, nullable=True)

    # Calibration snapshot
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    n_tgt = Column(Float, nullable=True)

    # Maker-checker
    submitted_by = Column(String(36), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Source for cloning
    cloned_from_id = Column(String(36), ForeignKey('product_versions.id'), nullable=True)

    change_summary = Column(Text, nullable=True)
