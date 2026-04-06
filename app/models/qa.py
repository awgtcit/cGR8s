"""
QA Analysis and QA Update models.
Maps to legacy: QA Analysis sheet
"""
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Date
from app.database import Base
from app.models.base import AuditMixin, VersionMixin, generate_uuid
from datetime import datetime, timezone


class QAAnalysis(Base, AuditMixin, VersionMixin):
    """QA analysis record – frozen result snapshot awaiting QA review."""
    __tablename__ = 'qa_analysis'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    process_order_id = Column(
        String(36), ForeignKey('process_orders.id'), nullable=False, index=True
    )
    npl_result_id = Column(
        String(36), ForeignKey('npl_results.id'), nullable=True
    )
    target_weight_result_id = Column(
        String(36), ForeignKey('target_weight_results.id'), nullable=True
    )

    status = Column(String(30), nullable=False, default='Pending', index=True)
    # Pending -> Updated -> Finalized

    # QA measured values (populated by QA team)
    qa_w_cig = Column(Float, nullable=True)
    qa_w_tob = Column(Float, nullable=True)
    qa_moisture = Column(Float, nullable=True)
    qa_nicotine = Column(Float, nullable=True)
    qa_tar = Column(Float, nullable=True)
    qa_co = Column(Float, nullable=True)

    # ── Date fields (cGR8s columns B, D) ──────────────────
    qr_date = Column(Date, nullable=True)           # Col B: QR Date (D-)
    npl_date = Column(Date, nullable=True)           # Col D: NPL Date (D+1)

    # ── Measurement fields (cGR8s columns N–AO, excl Y,Z,AG,AH) ──
    pack_ov = Column(Float, nullable=True)           # Col N: Pack OV
    lamina_cpi = Column(Float, nullable=True)        # Col O: Lamina CPI
    filling_power = Column(Float, nullable=True)     # Col P: Filling Power
    filling_power_corr = Column(Float, nullable=True)  # Col Q: Filling Power Corr
    maker_moisture = Column(Float, nullable=True)    # Col R: Maker Moisture
    ssi = Column(Float, nullable=True)               # Col S: SSI
    pan_pct = Column(Float, nullable=True)           # Col T: PAN%
    total_cig_length = Column(Float, nullable=True)  # Col U: Total Cig. Length
    circumference_mean = Column(Float, nullable=True)  # Col V: Circumference Mean
    circumference_sd = Column(Float, nullable=True)  # Col W: Circumference SD
    cig_dia = Column(Float, nullable=True)           # Col X: Cig Dia
    tobacco_weight_mean = Column(Float, nullable=True)  # Col Y: Tobacco Weight Mean
    tobacco_weight_sd = Column(Float, nullable=True)  # Col Z: Tobacco Weight SD
    tip_vf = Column(Float, nullable=True)            # Col AA: TIP VF
    tip_vf_sd = Column(Float, nullable=True)         # Col AB: TIP Vf SD
    filter_pd_mean = Column(Float, nullable=True)    # Col AC: Filter PD Mean
    filter_weight = Column(Float, nullable=True)     # Col AD: Filter Weight
    w_ntm = Column(Float, nullable=True)             # Col AD alt: W_NTM (legacy alias)
    plug_wrap_cu = Column(Float, nullable=True)      # Col AE: Plug Wrap CU
    tow = Column(String(100), nullable=True)         # Col AF: TOW
    cig_wt_mean = Column(Float, nullable=True)       # Col AG: Cig. Wt. Mean
    cig_wt_sd = Column(Float, nullable=True)         # Col AH: Cig. Wt. SD
    cig_pdo = Column(Float, nullable=True)           # Col AI: Cig PDO
    cig_hardness = Column(Float, nullable=True)      # Col AJ: Cig. Hardness
    cig_corr_hardness = Column(Float, nullable=True)  # Col AK: Cig. Corr. Hardness
    loose_shorts = Column(Float, nullable=True)      # Col AL: Loose Shorts
    plug_length = Column(Float, nullable=True)       # Col AM: Plug Length
    mc = Column(String(50), nullable=True)            # Col AN: MC (Machine)
    company = Column(String(100), nullable=True)     # Col AO: Company

    notes = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QAUpdate(Base, AuditMixin):
    """QA update/finalization record."""
    __tablename__ = 'qa_updates'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    qa_analysis_id = Column(
        String(36), ForeignKey('qa_analysis.id'), nullable=False, index=True
    )

    # Updated values from QA
    updated_w_cig = Column(Float, nullable=True)
    updated_w_tob = Column(Float, nullable=True)
    updated_moisture = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    finalized_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finalized_by = Column(String(36), nullable=True)
