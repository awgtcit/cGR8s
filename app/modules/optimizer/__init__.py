"""Product Run Optimizer module."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction
from app.repositories import (
    ProcessOrderRepository, KeyVariableRepository, TargetWeightResultRepository,
    OptimizerRunRepository, OptimizerInputRepository, OptimizerResultRepository,
    OptimizerLimitRepository,
)
from app.services.optimizer import ProductRunOptimizer, OptimizerConfig, OptimizerInput as OptInput
from app.services.target_weight_calc import TargetWeightCalculator, TargetWeightInput
from app.rules.validators import optimizer_input_engine
from app.utils.helpers import flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('optimizer', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.OPTIMIZER_VIEW)
def index():
    from app.utils.helpers import paginate_args
    page, per_page = paginate_args(request.args)
    repo = OptimizerRunRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page)
    # Build PO number lookup for display (single bulk query)
    po_repo = ProcessOrderRepository(g.db)
    po_ids = list({r.process_order_id for r in result.get('items', []) if r.process_order_id})
    po_lookup = po_repo.get_po_number_map(po_ids)
    return render_template('optimizer/index.html', po_lookup=po_lookup, **result)


@bp.route('/run/<process_order_id>', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.OPTIMIZER_RUN)
def run(process_order_id):
    po_repo = ProcessOrderRepository(g.db)
    po = po_repo.get_by_id(process_order_id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', process_order_id)

    # Get latest key variables (base) + FG for physical params
    from app.repositories import FGCodeRepository
    kv_repo = KeyVariableRepository(g.db)
    kvs = kv_repo.get_all(filters={'process_order_id': process_order_id})
    kv = kvs[-1] if kvs else None
    fg = FGCodeRepository(g.db).get_by_id(po.fg_code_id) if po.fg_code_id else None

    # Tolerance limits (informational display). NOTE: model uses min_value/max_value.
    limit_repo = OptimizerLimitRepository(g.db)
    limits = limit_repo.get_limits_for_fg(po.fg_code_id)
    limits_dict = {}
    for lim in limits:
        limits_dict[lim.parameter_name] = {
            'lower': float(lim.min_value) if lim.min_value is not None else None,
            'upper': float(lim.max_value) if lim.max_value is not None else None,
        }

    if request.method == 'POST':
        data = request.form.to_dict()
        method = data.get('method', 'direct')

        if not kv:
            flash_error('Calculate Target Weight for this order before optimizing.')
            return render_template('optimizer/run.html', po=po, kv=kv,
                                   limits=limits_dict, data=data, errors=[])

        base_kv = {'n_bld': float(kv.n_bld or 0), 'p_cu': float(kv.p_cu or 0),
                   't_vnt': float(kv.t_vnt or 0), 'f_pd': float(kv.f_pd or 0),
                   'm_ip': float(kv.m_ip or 0)}
        calibration = _calibration(kv, fg)
        fg_info = _fg_info(fg)
        forward = _make_forward(g.db, calibration, fg_info)

        base_out = _forward_full(g.db, base_kv, calibration, fg_info)
        stage = reached = None

        if method == 'direct':
            try:
                target = float(data.get('direct_target_wcig') or 0)
            except (TypeError, ValueError):
                target = 0
            if target <= 0:
                flash_error('Enter a target cigarette weight (mg).')
                return render_template('optimizer/run.html', po=po, kv=kv,
                                       limits=limits_dict, data=data, errors=[])
            from app.services.optimizer_solver import optimize_to_target
            sol = optimize_to_target(base_kv, target, forward,
                                     constants=_formula_constants(g.db),
                                     stage_tols=_stage_tols(g.db))
            revised_kv = {**base_kv, **sol['revised']}
            stage, reached = sol['stage'], sol['reached']
        elif method == 'adjustment':
            revised_kv = dict(base_kv)
            for k in base_kv:
                d = data.get(f'adjustment_{k}')
                if d:
                    revised_kv[k] = base_kv[k] + float(d)
        else:  # manual
            revised_kv = dict(base_kv)
            for k in base_kv:
                v = data.get(f'manual_{k}')
                if v:
                    revised_kv[k] = float(v)

        opt_out = _forward_full(g.db, revised_kv, calibration, fg_info)
        within = reached if reached is not None else True

        # persist run + input + result
        run_repo = OptimizerRunRepository(g.db)
        opt_run = run_repo.create({'process_order_id': process_order_id,
                                   'method': method, 'is_verified': bool(within)})
        OptimizerInputRepository(g.db).create({
            'optimizer_run_id': opt_run.id,
            **{f'base_{k}': v for k, v in base_kv.items()},
            'direct_cig_weight': float(data.get('direct_target_wcig') or 0) if method == 'direct' else None,
        })
        OptimizerResultRepository(g.db).create({
            'optimizer_run_id': opt_run.id,
            **{f'opt_{k}': v for k, v in revised_kv.items()},
            'opt_w_cig': opt_out['output_data']['w_cig'],
            'opt_w_tob': opt_out['output_data']['w_tob'],
            'opt_w_dry': opt_out['output_data']['w_dry'],
            'opt_total_dilution': opt_out['interim_output']['total_dilution'],
            'opt_filtration_pct': opt_out['interim_output']['filtration_pct'],
            'within_tolerance': bool(within),
        })
        g.db.commit()
        AuditLogger.log(AuditAction.OPTIMIZE, 'Optimizer', entity_id=opt_run.id,
                        after_value={'method': method, 'stage': stage, 'reached': reached},
                        module='optimizer')
        flash_success('Optimization completed')

        names = {'n_bld': 'N_BLD', 'p_cu': 'P_CU', 't_vnt': 'T_VNT', 'f_pd': 'F_PD', 'm_ip': 'M_IP'}
        variables = [{
            'name': names[k], 'original': base_kv[k], 'optimized': revised_kv[k],
            'delta': revised_kv[k] - base_kv[k], 'within_limit': _within(k, revised_kv[k], limits_dict),
        } for k in base_kv]
        base_wcig = base_out['output_data']['w_cig'] or 0
        result = {
            'optimized_cigarette_weight': opt_out['output_data']['w_cig'],
            'optimized_tobacco_weight': opt_out['output_data']['w_tob'],
            'variance_percent': ((opt_out['output_data']['w_cig'] - base_wcig) / base_wcig * 100) if base_wcig else 0,
            'within_tolerance': bool(within),
            'stage': stage, 'reached': reached,
            'target_wcig': float(data.get('direct_target_wcig') or 0) if method == 'direct' else None,
            'base_cigarette_weight': base_wcig,
        }
        return render_template('optimizer/result.html', po=po, fg=fg, run=opt_run,
                               result=result, variables=variables, limits=limits, method=method)

    return render_template('optimizer/run.html',
                           po=po, kv=kv, limits=limits_dict, data={}, errors=[])


def _calibration(kv, fg):
    cal = {'alpha': float(kv.alpha or 0), 'beta': float(kv.beta or 0),
           'gamma': float(kv.gamma or 0), 'delta': float(kv.delta or 0),
           'n_tgt': float(kv.n_tgt or 0)}
    if not any(cal.values()) and fg:  # fall back to resolved calibration
        from app.modules.fg_codes import get_calibration_constants
        c = get_calibration_constants(fg.fg_code)
        cal.update({k: float(c.get(k) or 0) for k in cal})
    return cal


def _fg_info(fg):
    from app.modules.fg_codes import get_tobacco_constant
    return {'c_plg': int(fg.c_plg or 1) if fg and fg.c_plg else 1,
            'ntm_wt_mean': float(fg.ntm_wt_mean or 0) if fg else 0,
            'tobacco_constant': get_tobacco_constant()}


def _forward_full(session, kv, calibration, fg_info):
    from app.services import formula_service
    return formula_service.compute(session, 'target_weight', {**kv, **calibration, **fg_info})


def _make_forward(session, calibration, fg_info):
    def fwd(kv):
        return _forward_full(session, kv, calibration, fg_info)['output_data']['w_cig']
    return fwd


def _formula_constants(session):
    try:
        from app.repositories import FormulaConstantRepository
        return FormulaConstantRepository(session).get_constants_dict()
    except Exception:
        return {}


def _stage_tols(session):
    """KP-TOLERANCE stage bands from the lookups (category 'kp_tolerance'),
    falling back to the built-in defaults. display_name like 'S1: 10, S2: 20, S3: 75'."""
    import re
    from app.services.optimizer_solver import DEFAULT_STAGE_TOLS
    from app.repositories import LookupRepository
    label_to_param = {'input moisture': 'm_ip', 'tip ventilation': 't_vnt',
                      'filter pd': 'f_pd', 'cig. paper cu': 'p_cu',
                      'paper cu': 'p_cu', 'blend nic': 'n_bld'}
    try:
        rows = LookupRepository(session).get_by_category('kp_tolerance')
    except Exception:
        rows = []
    if not rows:
        return DEFAULT_STAGE_TOLS
    stages = [{}, {}, {}, {}]
    for r in rows:
        code = (r.code or '').lower()
        param = next((p for key, p in label_to_param.items() if key in code), None)
        if not param:
            continue
        nums = re.findall(r'S\d\s*:\s*([0-9.]+)', r.display_name or '')
        for i, n in enumerate(nums[:3]):
            try:
                stages[i][param] = float(n)
            except ValueError:
                pass
    # stage 3 also gets the widest of the parsed; stage 4 = best-effort
    for p in ('t_vnt', 'f_pd', 'm_ip', 'p_cu', 'n_bld'):
        stages[3][p] = 1e9
    return stages if any(stages[0]) else DEFAULT_STAGE_TOLS


def _within(param, value, limits_dict):
    lim = limits_dict.get(param) or limits_dict.get(param.upper())
    if not lim:
        return True
    if lim.get('lower') is not None and value < lim['lower']:
        return False
    if lim.get('upper') is not None and value > lim['upper']:
        return False
    return True
