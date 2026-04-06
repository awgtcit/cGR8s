"""
FG Code / SKU master model.
Maps to legacy: GTIN / master reference sheet + Targets & Limits
"""
from sqlalchemy import Column, String, Float, Integer, Boolean
from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, VersionMixin, generate_uuid


class FGCode(Base, AuditMixin, SoftDeleteMixin, VersionMixin):
    """Finished-Goods code master table – one row per unique SKU."""
    __tablename__ = 'fg_codes'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fg_code = Column(String(50), unique=True, nullable=False, index=True)
    brand = Column(String(100), nullable=True)
    fg_gtin = Column(String(50), nullable=True)
    format = Column(String(50), nullable=True)
    tow_used = Column(String(100), nullable=True)
    filter_code = Column(String(50), nullable=True)
    blend_code = Column(String(50), nullable=True, index=True)
    blend = Column(String(100), nullable=True)
    blend_gtin = Column(String(50), nullable=True)
    cig_length = Column(Float, nullable=True)
    tobacco_rod_length = Column(Float, nullable=True)
    filter_length = Column(Float, nullable=True)
    plug_length = Column(Float, nullable=True)
    cig_code = Column(String(50), nullable=True)
    c_plg = Column(Integer, nullable=True)  # number of cuts
    is_active = Column(Boolean, default=True, nullable=False)

    # ── Targets & Limits (from Excel "Targets & Limits" sheet) ────────
    family_name = Column(String(100), nullable=True)

    # Circumference
    circumference_mean = Column(Float, nullable=True)
    circumference_mean_ul = Column(Float, nullable=True)
    circumference_mean_ll = Column(Float, nullable=True)
    circumference_sd_max = Column(Float, nullable=True)

    # Cigarette PDO
    cig_pdo = Column(Float, nullable=True)
    cig_pdo_ul = Column(Float, nullable=True)
    cig_pdo_ll = Column(Float, nullable=True)

    # Tip Ventilation
    tip_ventilation = Column(Float, nullable=True)
    tip_ventilation_ul = Column(Float, nullable=True)
    tip_ventilation_ll = Column(Float, nullable=True)
    tip_ventilation_sd_max = Column(Float, nullable=True)

    # Weight
    ntm_wt_mean = Column(Float, nullable=True)
    cig_wt_sd_max = Column(Float, nullable=True)

    # Filter PD
    filter_pd = Column(Float, nullable=True)
    filter_pd_ul = Column(Float, nullable=True)
    filter_pd_ll = Column(Float, nullable=True)

    # Hardness
    cig_hardness = Column(Float, nullable=True)
    cig_hardness_ul = Column(Float, nullable=True)
    cig_hardness_ll = Column(Float, nullable=True)
    cig_corrected_hardness = Column(Float, nullable=True)
    loose_shorts_max = Column(Float, nullable=True)

    # Filter
    filter_weight = Column(Float, nullable=True)

    # Moisture
    c48_moisture = Column(Float, nullable=True)
    c48_moisture_ul = Column(Float, nullable=True)
    c48_moisture_ll = Column(Float, nullable=True)
    maker_moisture = Column(Float, nullable=True)
    maker_moisture_ul = Column(Float, nullable=True)
    maker_moisture_ll = Column(Float, nullable=True)

    # Pack OV & SSI
    pack_ov = Column(Float, nullable=True)
    pack_ov_ul = Column(Float, nullable=True)
    pack_ov_ll = Column(Float, nullable=True)
    ssi = Column(Float, nullable=True)
    ssi_ul = Column(Float, nullable=True)
    ssi_ll = Column(Float, nullable=True)

    # Filling Power
    lamina_cpi = Column(Float, nullable=True)
    filling_power = Column(Float, nullable=True)
    filling_power_ul = Column(Float, nullable=True)
    filling_power_ll = Column(Float, nullable=True)
    filling_power_corrected_ul = Column(Float, nullable=True)
    pan_pct_max = Column(Float, nullable=True)

    # Additional
    filter_desc = Column(String(200), nullable=True)
    plug_wrap_cu = Column(Float, nullable=True)
    target_nic = Column(Float, nullable=True)
