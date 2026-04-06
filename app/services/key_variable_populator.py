"""
Key Variable Populator – auto-populates default key variables and
calibration constants for a given FG Code using cascade logic.

Cascade order for N_BLD:
  1. Latest ProcessOrderKeyVariable for any PO with the same blend_code
  2. BlendMaster.n_bld
  3. Latest TobaccoBlendAnalysis.nic_dry for matching blend_name

P_CU lookup:
  Extract size prefix from format (e.g. KS20SE → KS), then look up
  Lookup(category='size_cu', code='KS') → parse numeric value from
  display_name "KS = 50".

Constants (Alpha, Beta, Delta):
  From FormulaConstant table.

Gamma:
  From GammaConstant table by (format, plug_length, n_tgt < 0.3).

N_tgt:
  From SKU.nicotine where SKU.cig_code matches FGCode.cig_code.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KeyVariablePopulator:
    """Auto-populates key variable defaults for a given FG Code."""

    def __init__(self, session):
        self.session = session

    def get_defaults(self, fg) -> dict:
        """Return a dict of default key variables for the given FGCode entity."""
        from app.repositories import (
            FormulaConstantRepository, GammaConstantRepository,
            KeyVariableRepository, LookupRepository, SKURepository,
            TobaccoBlendAnalysisRepository, BlendMasterRepository,
            FGCodeRepository, ProcessOrderRepository,
        )

        result = {}

        # ── N_tgt from SKU ───────────────────────────────────────
        n_tgt = self._get_n_tgt(fg)
        result['n_tgt'] = n_tgt

        # ── Constants from FormulaConstant table ─────────────────
        try:
            fc_repo = FormulaConstantRepository(self.session)
            constants = fc_repo.get_constants_dict()
        except Exception:
            logger.warning('FormulaConstant table not available, using defaults')
            constants = {}
        result['alpha'] = constants.get('Alpha', 10.0)
        result['beta'] = constants.get('Beta', -0.043)
        result['delta'] = constants.get('Delta', -0.056)

        # ── Gamma from GammaConstant lookup ──────────────────────
        gamma_val = self._get_gamma(fg, n_tgt)
        result['gamma'] = gamma_val

        # ── N_BLD cascade ────────────────────────────────────────
        result['n_bld'] = self._get_n_bld(fg)

        # ── P_CU from Size/CU lookup ────────────────────────────
        result['p_cu'] = self._get_p_cu(fg)

        # ── T_VNT from FG targets ───────────────────────────────
        result['t_vnt'] = float(fg.tip_ventilation or 0)

        # ── F_PD from FG targets ────────────────────────────────
        result['f_pd'] = float(fg.filter_pd or 0)

        # ── M_IP from FG targets (maker moisture) ───────────────
        result['m_ip'] = round(float(fg.maker_moisture or 0), 4)

        # ── C_PLG and NTM from FG ───────────────────────────────
        result['c_plg'] = int(fg.c_plg or 0)
        result['ntm_wt_mean'] = float(fg.ntm_wt_mean or 0)

        return result

    def get_last_calculation(self, fg) -> Optional[dict]:
        """Get the last TargetWeightResult for any PO of this FG Code."""
        from app.repositories import (
            ProcessOrderRepository, TargetWeightResultRepository,
        )
        po_repo = ProcessOrderRepository(self.session)
        tw_repo = TargetWeightResultRepository(self.session)

        orders = po_repo.get_by_fg_code(fg.id)
        for po in orders:
            result = tw_repo.get_by_process_order(po.id)
            if result:
                return {
                    'stage1_dilution': result.stage1_dilution,
                    'stage2_dilution': result.stage2_dilution,
                    'total_dilution': result.total_dilution,
                    'filtration_pct': result.filtration_pct,
                    'total_nicotine_demand': result.total_nicotine_demand,
                    'stage1_pacifying_nicotine_demand': result.stage1_pacifying_nicotine_demand,
                    'stage2_pacifying_nicotine_demand': result.stage2_pacifying_nicotine_demand,
                    'total_pacifying_nicotine_demand': result.total_pacifying_nicotine_demand,
                    'total_filtration_pct': result.total_filtration_pct,
                    'w_dry': result.w_dry,
                    'w_tob': result.w_tob,
                    'w_cig': result.w_cig,
                    'w_ntm': result.w_ntm,
                    'tw': result.tw,
                    'input_n_bld': result.input_n_bld,
                    'input_p_cu': result.input_p_cu,
                    'input_t_vnt': result.input_t_vnt,
                    'input_f_pd': result.input_f_pd,
                    'input_m_ip': result.input_m_ip,
                    'input_alpha': result.input_alpha,
                    'input_beta': result.input_beta,
                    'input_gamma': result.input_gamma,
                    'input_delta': result.input_delta,
                    'input_n_tgt': result.input_n_tgt,
                    'calculated_at': result.calculated_at,
                }
        return None

    def _get_n_tgt(self, fg) -> float:
        """N_tgt from SKU.nicotine where SKU.cig_code matches FG.cig_code."""
        if not fg.cig_code:
            return float(fg.target_nic or 0)

        from app.models.sku import SKU
        sku = self.session.query(SKU).filter(
            SKU.cig_code == fg.cig_code,
            SKU.is_active == True,
            SKU.is_deleted == False,  # noqa: E712
        ).first()
        if sku and sku.nicotine is not None:
            return float(sku.nicotine)
        return float(fg.target_nic or 0)

    def _get_gamma(self, fg, n_tgt: float) -> float:
        """Gamma from GammaConstant lookup table."""
        try:
            from app.repositories import GammaConstantRepository
            gc_repo = GammaConstantRepository(self.session)

            fmt = (fg.format or '').strip().upper()

            plug_len = int(fg.plug_length or 0)
            condition = n_tgt < 0.3

            gc = gc_repo.get_gamma(fmt, plug_len, condition)
            if gc:
                return gc.value

            logger.warning('Gamma: no entry found for format=%s plug_length=%s condition=%s',
                           fmt, plug_len, condition)
        except Exception:
            logger.warning('GammaConstant table not available, using default 0.0')
        return 0.0

    def _get_n_bld(self, fg) -> float:
        """N_BLD cascade: last key_var for same blend → BlendMaster → TobaccoBlendAnalysis."""
        blend_code = fg.blend_code
        if not blend_code:
            return 0.0

        # 1) Latest key variable for any FG with the same blend_code
        from app.models.fg_code import FGCode
        from app.models.process_order import ProcessOrder
        from app.models.key_variable import ProcessOrderKeyVariable

        last_kv = (
            self.session.query(ProcessOrderKeyVariable)
            .join(ProcessOrder, ProcessOrderKeyVariable.process_order_id == ProcessOrder.id)
            .join(FGCode, ProcessOrder.fg_code_id == FGCode.id)
            .filter(FGCode.blend_code == blend_code)
            .order_by(ProcessOrderKeyVariable.created_at.desc())
            .first()
        )
        if last_kv and last_kv.n_bld:
            return float(last_kv.n_bld)

        # 2) BlendMaster.n_bld
        from app.repositories import BlendMasterRepository
        blend_repo = BlendMasterRepository(self.session)
        blend = blend_repo.get_by_blend_code(blend_code)
        if blend and blend.n_bld:
            return float(blend.n_bld)

        # 3) Latest TobaccoBlendAnalysis.nic_dry for matching blend_name
        from app.models.tobacco_blend_analysis import TobaccoBlendAnalysis
        tba = (
            self.session.query(TobaccoBlendAnalysis)
            .filter(TobaccoBlendAnalysis.blend_name == blend_code)
            .order_by(
                TobaccoBlendAnalysis.period_year.desc(),
                TobaccoBlendAnalysis.period_month.desc(),
            )
            .first()
        )
        if tba and tba.nic_dry:
            return float(tba.nic_dry)

        return 0.0

    def _get_p_cu(self, fg) -> float:
        """P_CU from Size/CU lookup: extract size prefix from format."""
        fmt = fg.format or ''
        match = re.match(r'^([A-Za-z]+)', fmt)
        if not match:
            return 0.0

        size_prefix = match.group(1).upper()

        from app.repositories import LookupRepository
        lookup_repo = LookupRepository(self.session)
        lookups = lookup_repo.get_by_category('size_cu')

        for lu in lookups:
            if lu.code and lu.code.upper() == size_prefix:
                # Parse numeric value from display_name like "KS = 50"
                num_match = re.search(r'=\s*(\d+(?:\.\d+)?)', lu.display_name or '')
                if num_match:
                    return float(num_match.group(1))
        return 0.0
