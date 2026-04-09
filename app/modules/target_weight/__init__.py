"""Target Weight Calculator module."""
from flask import Blueprint, render_template, request, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction
from app.repositories import (
    FGCodeRepository, ProcessOrderRepository, KeyVariableRepository,
    TargetWeightResultRepository, CalibrationConstantRepository,
    PhysicalParameterRepository,
)
from app.services.target_calculation_service import TargetCalculationService
from app.services.key_variable_populator import KeyVariablePopulator
from app.models.key_variable import ProcessOrderKeyVariable
from app.models.target_weight_result import TargetWeightResult
from app.rules.validators import key_variable_engine
from app.utils.helpers import flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('target_weight', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.TARGET_WEIGHT_VIEW)
def index():
    """Target weight calculator landing – select process order."""
    repo = ProcessOrderRepository(g.db)
    orders = repo.get_all()
    # Build FG code lookup for display
    fg_repo = FGCodeRepository(g.db)
    fg_code_ids = list({o.fg_code_id for o in orders if o.fg_code_id})
    fg_lookup = fg_repo.get_fg_code_map(fg_code_ids)
    return render_template('target_weight/index.html', orders=orders, fg_lookup=fg_lookup)


@bp.route('/calculate/<process_order_id>', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.TARGET_WEIGHT_CALCULATE)
def calculate(process_order_id):
    """Calculate target weight for a process order."""
    po_repo = ProcessOrderRepository(g.db)
    po = po_repo.get_by_id(process_order_id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', process_order_id)

    fg_repo = FGCodeRepository(g.db)
    fg = fg_repo.get_by_id(po.fg_code_id)

    # Use KeyVariablePopulator for auto-populated defaults
    populator = KeyVariablePopulator(g.db)
    defaults = populator.get_defaults(fg) if fg else {}
    last_calc = populator.get_last_calculation(fg) if fg else None

    if request.method == 'POST':
        data = request.form.to_dict()

        # Validate key variables
        engine = key_variable_engine()
        data['process_order_id'] = process_order_id
        result = engine.validate(data)
        if not result.is_valid:
            flash_error('Validation failed')
            return render_template('target_weight/calculate.html',
                                   po=po, fg=fg, defaults=defaults,
                                   last_calc=last_calc, data=data, errors=result.errors)

        # Build key variables dict
        kv_data = {
            'n_bld': float(data.get('n_bld', 0)),
            'p_cu': float(data.get('p_cu', 0)),
            't_vnt': float(data.get('t_vnt', 0)),
            'f_pd': float(data.get('f_pd', 0)),
            'm_ip': float(data.get('m_ip', 0)),
        }

        # Build calibration dict from form (these come from hidden/readonly fields)
        cal_data = {
            'alpha': float(data.get('alpha', defaults.get('alpha', 0))),
            'beta': float(data.get('beta', defaults.get('beta', 0))),
            'gamma': float(data.get('gamma', defaults.get('gamma', 0))),
            'delta': float(data.get('delta', defaults.get('delta', 0))),
            'n_tgt': float(data.get('n_tgt', defaults.get('n_tgt', 0))),
        }

        # FG info for calculation — W_NTM is user-editable
        fg_info = {
            'c_plg': defaults.get('c_plg', 1),
            'ntm_wt_mean': float(data.get('w_ntm', defaults.get('ntm_wt_mean', 0))),
        }

        # Save key variables
        kv_repo = KeyVariableRepository(g.db)
        kv_entity = ProcessOrderKeyVariable(
            process_order_id=process_order_id,
            n_bld=kv_data['n_bld'],
            p_cu=kv_data['p_cu'],
            t_vnt=kv_data['t_vnt'],
            f_pd=kv_data['f_pd'],
            m_ip=kv_data['m_ip'],
            alpha=cal_data['alpha'],
            beta=cal_data['beta'],
            gamma=cal_data['gamma'],
            delta=cal_data['delta'],
            n_tgt=cal_data['n_tgt'],
        )
        kv_repo.create(kv_entity)

        # Run calculation with correct formulas
        calc_result = TargetCalculationService.calculate_forward_target(
            kv_data, cal_data, fg_info
        )

        interim = calc_result['interim_output']
        output = calc_result['output_data']

        # Save results
        tw_repo = TargetWeightResultRepository(g.db)
        tw_entity = TargetWeightResult(
            process_order_id=process_order_id,
            stage1_dilution=interim['stage1_dilution'],
            stage2_dilution=interim['stage2_dilution'],
            total_dilution=interim['total_dilution'],
            filtration_pct=interim['filtration_pct'],
            total_nicotine_demand=interim['nicotine_filtration_pct'],
            stage1_pacifying_nicotine_demand=interim['nic_demand_stage1'],
            stage2_pacifying_nicotine_demand=interim['nic_demand_stage2'],
            total_pacifying_nicotine_demand=interim['nic_demand_total'],
            total_filtration_pct=interim['total_nicotine'],
            w_dry=output['w_dry'],
            w_tob=output['w_tob'],
            w_cig=output['w_cig'],
            w_ntm=output['w_ntm'],
            tw=output['tw'],
            # Input snapshots
            input_n_bld=kv_data['n_bld'],
            input_p_cu=kv_data['p_cu'],
            input_t_vnt=kv_data['t_vnt'],
            input_f_pd=kv_data['f_pd'],
            input_m_ip=kv_data['m_ip'],
            input_alpha=cal_data['alpha'],
            input_beta=cal_data['beta'],
            input_gamma=cal_data['gamma'],
            input_delta=cal_data['delta'],
            input_n_tgt=cal_data['n_tgt'],
        )
        tw_repo.create(tw_entity)

        # Update process order status
        from app.config.constants import ProcessOrderStatus
        po.status = ProcessOrderStatus.CALCULATED.value
        po_repo.update(po)
        g.db.commit()

        AuditLogger.log(AuditAction.CALCULATE, 'TargetWeight',
                        entity_id=process_order_id,
                        after_value={'interim': interim, 'output': output},
                        module='target_weight')
        flash_success('Target weight calculated successfully')

        return render_template('target_weight/result.html',
                               po=po, fg=fg,
                               interim=interim, output=output,
                               kv=kv_data, cal=cal_data)

    # GET: pre-fill form from last calculation or defaults
    prefill = {}
    if last_calc:
        # Pre-fill from last calculation inputs
        prefill = {
            'n_bld': last_calc.get('input_n_bld', defaults.get('n_bld', 0)),
            'p_cu': last_calc.get('input_p_cu', defaults.get('p_cu', 0)),
            't_vnt': last_calc.get('input_t_vnt', defaults.get('t_vnt', 0)),
            'f_pd': last_calc.get('input_f_pd', defaults.get('f_pd', 0)),
            'm_ip': last_calc.get('input_m_ip', defaults.get('m_ip', 0)),
            'w_ntm': last_calc.get('w_ntm', defaults.get('ntm_wt_mean', 0)),
        }
    else:
        prefill = {
            'n_bld': defaults.get('n_bld', 0),
            'p_cu': defaults.get('p_cu', 0),
            't_vnt': defaults.get('t_vnt', 0),
            'f_pd': defaults.get('f_pd', 0),
            'm_ip': defaults.get('m_ip', 0),
            'w_ntm': defaults.get('ntm_wt_mean', 0),
        }

    return render_template('target_weight/calculate.html',
                           po=po, fg=fg, defaults=defaults,
                           last_calc=last_calc, data=prefill, errors=[])
