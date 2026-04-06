"""
Domain-specific rule validators for Process Orders, NPL, Optimizer, and NPD.
"""
from app.config.constants import ProcessOrderStatus
from app.rules import (
    BaseRule, MandatoryFieldsRule, ValueRangeRule,
    StatusTransitionRule, RulesEngine, ValidationResult,
)


# ---------------------------------------------------------------------------
# Process Order Rules
# ---------------------------------------------------------------------------

PROCESS_ORDER_REQUIRED = [
    'process_order_number', 'fg_code_id', 'process_date',
]

PROCESS_ORDER_TRANSITIONS = {
    ProcessOrderStatus.DRAFT.value: [ProcessOrderStatus.CALCULATED.value],
    ProcessOrderStatus.CALCULATED.value: [
        ProcessOrderStatus.QA_PENDING.value,
        ProcessOrderStatus.DRAFT.value,
    ],
    ProcessOrderStatus.QA_PENDING.value: [ProcessOrderStatus.QA_UPDATED.value],
    ProcessOrderStatus.QA_UPDATED.value: [ProcessOrderStatus.COMPLETED.value],
    ProcessOrderStatus.COMPLETED.value: [ProcessOrderStatus.REPORT_GENERATED.value],
}


def process_order_create_engine(repository=None) -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(PROCESS_ORDER_REQUIRED))
    if repository:
        from app.rules import DuplicateCheckRule
        engine.add_rule(DuplicateCheckRule(repository, 'process_order_number', 'Process Order'))
    return engine


def process_order_status_engine() -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(StatusTransitionRule(PROCESS_ORDER_TRANSITIONS))
    return engine


# ---------------------------------------------------------------------------
# Key Variable Rules
# ---------------------------------------------------------------------------

KEY_VARIABLE_REQUIRED = ['process_order_id']

KEY_VARIABLE_RANGES = {
    'n_bld': (0, None),
    'p_cu': (0, None),
    't_vnt': (0, None),
    'f_pd': (0, None),
    'm_ip': (0, None),
}


def key_variable_engine() -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(KEY_VARIABLE_REQUIRED))
    engine.add_rule(ValueRangeRule(KEY_VARIABLE_RANGES))
    return engine


# ---------------------------------------------------------------------------
# NPL Input Rules
# ---------------------------------------------------------------------------

NPL_INPUT_REQUIRED = [
    'process_order_id',
]

NPL_INPUT_RANGES = {
    't_iss': (0, None),
    't_un': (0, None),
    'l_dst': (0, None),
    'l_win': (0, None),
    'l_flr': (0, None),
    'l_srt': (0, None),
    'l_dt': (0, None),
    'n_mc': (0, None),
    'n_cg': (0, None),
    'r_mkg': (0, None),
    'r_ndt': (0, None),
    'r_pkg': (0, None),
    'm_dsp': (0, 100),
    'm_dst': (0, 100),
}


def npl_input_engine() -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(NPL_INPUT_REQUIRED))
    engine.add_rule(ValueRangeRule(NPL_INPUT_RANGES))
    return engine


# ---------------------------------------------------------------------------
# Optimizer Rules
# ---------------------------------------------------------------------------

class ToleranceLimitRule(BaseRule):
    """Validates optimizer adjustments against tolerance limits."""

    def __init__(self, limits: dict):
        # limits = {'param_name': {'lower': x, 'upper': y}}
        self.limits = limits

    def validate(self, data: dict, context=None) -> ValidationResult:
        result = ValidationResult()
        adjustments = data.get('adjustments', {})
        for param, value in adjustments.items():
            if param in self.limits:
                lim = self.limits[param]
                lower = lim.get('lower')
                upper = lim.get('upper')
                try:
                    val = float(value)
                    if lower is not None and val < float(lower):
                        result.add_error(param, f'{param} below tolerance ({lower})', 'TOLERANCE')
                    if upper is not None and val > float(upper):
                        result.add_error(param, f'{param} exceeds tolerance ({upper})', 'TOLERANCE')
                except (ValueError, TypeError):
                    result.add_error(param, f'{param} must be numeric', 'TYPE')
        return result


def optimizer_input_engine(limits: dict = None) -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(['process_order_id', 'method']))
    if limits:
        engine.add_rule(ToleranceLimitRule(limits))
    return engine


# ---------------------------------------------------------------------------
# Product Development (NPD) Rules
# ---------------------------------------------------------------------------

FG_CODE_REQUIRED = [
    'fg_code', 'brand', 'format',
]


class MakerCheckerRule(BaseRule):
    """Ensures approver is different from the creator."""

    def validate(self, data: dict, context=None) -> ValidationResult:
        result = ValidationResult()
        created_by = data.get('created_by')
        approved_by = data.get('approved_by')
        if created_by and approved_by and created_by == approved_by:
            result.add_error(
                'approved_by',
                'Approver cannot be the same as the creator',
                'MAKER_CHECKER',
            )
        return result


def fg_code_engine(repository=None) -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(FG_CODE_REQUIRED))
    if repository:
        from app.rules import DuplicateCheckRule
        engine.add_rule(DuplicateCheckRule(repository, 'fg_code', 'FG Code'))
    return engine


def product_version_engine() -> RulesEngine:
    engine = RulesEngine()
    engine.add_rule(MandatoryFieldsRule(['fg_code_id', 'version_number']))
    engine.add_rule(MakerCheckerRule())
    return engine
