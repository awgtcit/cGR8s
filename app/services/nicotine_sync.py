"""Bidirectional sync between CalibrationConstant.n_tgt and SKU.nicotine."""
from flask import g
from app.repositories import FGCodeRepository, CalibrationConstantRepository, SKURepository
from app.models.calibration_constant import CalibrationConstant


def sync_nicotine(fg_code: str = None, fg_code_id=None, n_tgt_val: float = None):
    """Sync n_tgt value between CalibrationConstant and SKU.

    Provide either fg_code (string) or fg_code_id (int/str) to identify the FG record.
    Updates both CalibrationConstant.n_tgt and SKU.nicotine to the given value.

    Returns dict with 'cal' and 'sku' keys indicating what was updated.
    """
    fg_repo = FGCodeRepository(g.db)

    if fg_code:
        fg = fg_repo.get_by_code(fg_code)
    elif fg_code_id:
        fg = fg_repo.get_by_id(fg_code_id)
    else:
        return {'cal': False, 'sku': False}

    if not fg:
        return {'cal': False, 'sku': False}

    cal_updated = False
    sku_updated = False

    # Update CalibrationConstant
    cal_repo = CalibrationConstantRepository(g.db)
    cal = cal_repo.get_by_fg_code_id(fg.id)
    if cal:
        cal.n_tgt = n_tgt_val
        cal_updated = True
    else:
        cal = CalibrationConstant(fg_code_id=fg.id, n_tgt=n_tgt_val)
        g.db.add(cal)
        cal_updated = True

    # Update SKU
    sku_repo = SKURepository(g.db)
    sku = sku_repo.get_by_sku_code(fg.fg_code)
    if sku:
        sku.nicotine = n_tgt_val
        sku_updated = True

    return {'cal': cal_updated, 'sku': sku_updated, 'cal_obj': cal}
