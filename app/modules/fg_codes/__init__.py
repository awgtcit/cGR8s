"""Enhanced FG Codes module - VB Application style interface."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify, session
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions
from app.repositories import FGCodeRepository, ProcessOrderRepository, KeyVariableRepository, TargetWeightResultRepository
from app.models.key_variable import ProcessOrderKeyVariable
from app.models.target_weight_result import TargetWeightResult
from app.models.calibration_constant import CalibrationConstant
from app.services.target_calculation_service import TargetCalculationService
from app.services.nicotine_sync import sync_nicotine
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger
from app.config.constants import AuditAction

bp = Blueprint('fg_codes', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.FG_CODE_VIEW)
def index():
    """Main FG Codes interface - VB style with integrated features."""
    return render_template('fg_codes/main_interface.html')


@bp.route('/api/load-codes')
@require_auth
@require_permission(Permissions.FG_CODE_VIEW)
def api_load_codes():
    """Load FG codes with pagination - AJAX endpoint."""
    repo = FGCodeRepository(g.db)
    limit = request.args.get('limit', 200, type=int)
    load_all = request.args.get('all', '').lower() in ('true', '1', 'yes')
    search = request.args.get('q', '').strip()

    if load_all:
        # Load all codes
        codes = repo.get_all()
    else:
        # Load limited number
        codes = repo.get_limited(limit=limit, search=search)

    total_count = repo.count_all()
    loaded_count = len(codes)

    result = {
        'codes': [{'id': c.id, 'fg_code': c.fg_code, 'brand': c.brand, 'format': c.format}
                  for c in codes],
        'total_count': total_count,
        'loaded_count': loaded_count,
        'limit': None if load_all else limit
    }

    return jsonify(result)


@bp.route('/api/sku-details/<fg_code>')
@require_auth
@require_permission(Permissions.FG_CODE_VIEW)
def api_sku_details(fg_code):
    """Get detailed SKU information for selected FG Code."""
    repo = FGCodeRepository(g.db)
    fg = repo.get_by_code(fg_code)

    if not fg:
        return jsonify({'error': 'FG Code not found'}), 404

    # Get key variables for this FG code
    key_vars = get_key_variables(fg_code)

    # Get calibration constants
    calibration = get_calibration_constants(fg_code)

    # Get last run date
    po_repo = ProcessOrderRepository(g.db)
    last_run = po_repo.get_last_run_date(fg.id)

    result = {
        'fg_details': {
            'fg_code': fg.fg_code,
            'brand': fg.brand,
            'fg_gtin': fg.fg_gtin,
            'format': fg.format,
            'tow_used': fg.tow_used,
            'filter_code': fg.filter_code
        },
        'blend_details': {
            'blend_code': fg.blend_code,
            'blend': fg.blend,
            'blend_gtin': fg.blend_gtin
        },
        'physical_params': {
            'cig_length': fg.cig_length,
            'tobacco_rod_length': fg.tobacco_rod_length,
            'filter_length': fg.filter_length,
            'plug_length': fg.plug_length,
            'cig_code': fg.cig_code,
            'c_plg': fg.c_plg
        },
        'targets': {
            'family_name': fg.family_name,
            'circumference_mean': fg.circumference_mean,
            'circumference_ul': fg.circumference_mean_ul,
            'circumference_ll': fg.circumference_mean_ll,
            'circumference_sd': fg.circumference_sd_max,
            'cig_pdo': fg.cig_pdo,
            'cig_pdo_ul': fg.cig_pdo_ul,
            'cig_pdo_ll': fg.cig_pdo_ll,
            'tip_ventilation': fg.tip_ventilation,
            'tip_ventilation_ul': fg.tip_ventilation_ul,
            'tip_ventilation_ll': fg.tip_ventilation_ll,
            'tip_ventilation_sd': fg.tip_ventilation_sd_max,
            'ntm_wt_mean': fg.ntm_wt_mean,
            'cig_wt_sd_max': fg.cig_wt_sd_max,
            'filter_pd': fg.filter_pd,
            'filter_pd_ul': fg.filter_pd_ul,
            'filter_pd_ll': fg.filter_pd_ll,
            'cig_hardness': fg.cig_hardness,
            'cig_hardness_ul': fg.cig_hardness_ul,
            'cig_hardness_ll': fg.cig_hardness_ll,
            'cig_corrected_hardness': fg.cig_corrected_hardness,
            'loose_shorts_max': fg.loose_shorts_max,
            'filter_weight': fg.filter_weight,
            'c48_moisture': fg.c48_moisture,
            'c48_moisture_ul': fg.c48_moisture_ul,
            'c48_moisture_ll': fg.c48_moisture_ll,
            'maker_moisture': fg.maker_moisture,
            'maker_moisture_ul': fg.maker_moisture_ul,
            'maker_moisture_ll': fg.maker_moisture_ll,
            'pack_ov': fg.pack_ov,
            'pack_ov_ul': fg.pack_ov_ul,
            'pack_ov_ll': fg.pack_ov_ll,
            'ssi': fg.ssi,
            'ssi_ul': fg.ssi_ul,
            'ssi_ll': fg.ssi_ll,
            'lamina_cpi': fg.lamina_cpi,
            'filling_power': fg.filling_power,
            'filling_power_ul': fg.filling_power_ul,
            'filling_power_ll': fg.filling_power_ll,
            'filling_power_corrected_ul': fg.filling_power_corrected_ul,
            'pan_pct_max': fg.pan_pct_max,
            'filter_desc': fg.filter_desc,
            'plug_wrap_cu': fg.plug_wrap_cu,
            'target_nic': fg.target_nic,
        },
        'key_variables': key_vars,
        'calibration': calibration,
        'last_run_date': last_run.strftime('%Y-%m-%d') if last_run else None
    }

    return jsonify(result)


@bp.route('/api/calculate-target', methods=['POST'])
@require_auth
@require_permission(Permissions.TARGET_WEIGHT_CALCULATE)
def api_calculate_target():
    """Calculate forward target weights."""
    data = request.get_json()

    # Get key variables from request
    key_vars = data.get('key_variables', {})
    calibration = data.get('calibration', {})
    fg_info = data.get('fg_info', {})

    # Validate input data
    if not TargetCalculationService.validate_key_variables(key_vars):
        return jsonify({'error': 'Invalid key variables'}), 400

    if not TargetCalculationService.validate_calibration_constants(calibration):
        return jsonify({'error': 'Invalid calibration constants'}), 400

    # Perform forward target calculation using service
    result = TargetCalculationService.calculate_forward_target(key_vars, calibration, fg_info)

    return jsonify(result)


@bp.route('/api/update-n-target', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def api_update_n_target():
    """Update N Target (nicotine) with bidirectional sync between CalibrationConstant and SKU."""
    data = request.get_json()
    fg_code = str(data.get('fg_code', '')).strip()
    n_tgt_raw = data.get('n_tgt')

    if not fg_code or n_tgt_raw is None:
        return jsonify({'error': 'Missing fg_code or n_tgt'}), 400

    try:
        n_tgt_val = float(n_tgt_raw)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid n_tgt value'}), 400

    fg_repo = FGCodeRepository(g.db)
    fg = fg_repo.get_by_code(fg_code)
    if not fg:
        return jsonify({'error': 'FG Code not found'}), 404

    result = sync_nicotine(fg_code=fg_code, n_tgt_val=n_tgt_val)

    g.db.commit()

    AuditLogger.log(AuditAction.UPDATE, 'CalibrationConstant',
                    entity_id=result.get('cal_obj').id if result.get('cal_obj') else None,
                    after_value={'n_tgt': n_tgt_val, 'fg_code': fg_code, 'sku_synced': result['sku']},
                    module='fg_codes')

    return jsonify({'success': True, 'n_tgt': n_tgt_val})


@bp.route('/api/process-order/create', methods=['POST'])
@require_auth
@require_permission(Permissions.PROCESS_ORDER_CREATE)
def api_create_process_order():
    """Create process order from FG selection."""
    data = request.get_json()

    fg_code = str(data.get('fg_code', ''))
    process_date = data.get('process_date')
    process_order_id = str(data.get('process_order_id', ''))
    key_variables = data.get('key_variables', {})
    calibration = data.get('calibration', {})
    calculation_results = data.get('calculation_results', {})

    # Validate required fields
    if not all([fg_code, process_date, process_order_id]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Get FG Code record to obtain the database ID
    repo = FGCodeRepository(g.db)
    fg = repo.get_by_code(fg_code)
    if not fg:
        return jsonify({'error': 'FG Code not found'}), 404

    # Check for existing PO with same number AND date (composite key)
    po_repo = ProcessOrderRepository(g.db)
    existing_po = po_repo.get_by_order_number_and_date(process_order_id, process_date)

    if existing_po:
        # Verify user has edit permission for updates
        perms = session.get('sso_permissions', [])
        if Permissions.PROCESS_ORDER_EDIT not in perms:
            return jsonify({'error': 'Missing permission to update Process Order'}), 403

        # Update existing PO's key variables and calculation results
        update_key_variables(existing_po.id, key_variables, calibration)

        if calculation_results:
            update_calculation_results(existing_po.id, calculation_results, key_variables, calibration)

        # Update process date if changed
        existing_po.process_date = process_date
        g.db.commit()

        AuditLogger.log(AuditAction.UPDATE, 'ProcessOrder',
                        entity_id=existing_po.id,
                        after_value={'key_variables': key_variables, 'calibration': calibration},
                        module='fg_codes')

        return jsonify({'success': True, 'process_order_id': existing_po.id, 'updated': True})

    # Create process order record
    po_data = {
        'fg_code_id': fg.id,
        'process_order_number': process_order_id,
        'process_date': process_date,
        'status': 'Draft'
    }

    po = po_repo.create(po_data)
    g.db.flush()

    # Save key variables and calibration constants
    save_key_variables(po.id, key_variables, calibration)

    # Save calculation results if available
    if calculation_results:
        save_calculation_results(po.id, calculation_results, key_variables, calibration)

    g.db.commit()

    AuditLogger.log(AuditAction.CREATE, 'ProcessOrder',
                    entity_id=po.id, after_value=po_data, module='fg_codes')

    return jsonify({'success': True, 'process_order_id': po.id})


def get_key_variables(fg_code):
    """Get auto-populated key variables for FG code using KeyVariablePopulator."""
    from flask import g
    from app.services.key_variable_populator import KeyVariablePopulator

    repo = FGCodeRepository(g.db)
    fg = repo.get_by_code(fg_code)
    if not fg:
        return {'n_bld': 0.0, 'p_cu': 0.0, 't_vnt': 0.0, 'f_pd': 0.0, 'm_ip': 0.0}

    populator = KeyVariablePopulator(g.db)
    defaults = populator.get_defaults(fg)

    return {
        'n_bld': defaults.get('n_bld', 0.0),
        'p_cu': defaults.get('p_cu', 0.0),
        't_vnt': defaults.get('t_vnt', 0.0),
        'f_pd': defaults.get('f_pd', 0.0),
        'm_ip': defaults.get('m_ip', 0.0),
    }


def get_calibration_constants(fg_code):
    """Get calibration constants for FG code.

    Priority: stored CalibrationConstant record > KeyVariablePopulator defaults.
    """
    from flask import g
    from app.services.key_variable_populator import KeyVariablePopulator
    from app.repositories import CalibrationConstantRepository

    repo = FGCodeRepository(g.db)
    fg = repo.get_by_code(fg_code)
    if not fg:
        return {'alpha': 0.0, 'beta': 0.0, 'gamma': 0.0, 'delta': 0.0, 'n_tgt': 0.0,
                'gamma_format': '', 'gamma_plug_length': 0, 'gamma_condition': ''}

    # Check for stored calibration constants first
    cal_repo = CalibrationConstantRepository(g.db)
    stored = cal_repo.get_by_fg_code_id(fg.id)

    # Always compute defaults for fallback and gamma lookup metadata
    populator = KeyVariablePopulator(g.db)
    defaults = populator.get_defaults(fg)

    n_tgt = defaults.get('n_tgt', 0.0)
    fmt = (fg.format or '').strip().upper()
    plug_len = int(fg.plug_length or 0)
    cond = n_tgt < 0.3

    # Use stored values when available, fallback to computed defaults
    if stored:
        alpha = stored.alpha if stored.alpha is not None else defaults.get('alpha', 0.0)
        beta = stored.beta if stored.beta is not None else defaults.get('beta', 0.0)
        gamma = stored.gamma if stored.gamma is not None else defaults.get('gamma', 0.0)
        delta = stored.delta if stored.delta is not None else defaults.get('delta', 0.0)
        n_tgt_val = stored.n_tgt if stored.n_tgt is not None else n_tgt
        cond = n_tgt_val < 0.3
    else:
        alpha = defaults.get('alpha', 0.0)
        beta = defaults.get('beta', 0.0)
        gamma = defaults.get('gamma', 0.0)
        delta = defaults.get('delta', 0.0)
        n_tgt_val = n_tgt

    return {
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma,
        'delta': delta,
        'n_tgt': n_tgt_val,
        'gamma_format': fmt,
        'gamma_plug_length': plug_len,
        'gamma_condition': 'TRUE' if cond else 'FALSE',
    }



def _apply_key_variables(kv, key_variables, calibration=None):
    """Apply key variable and calibration values to a model instance."""
    kv.n_bld = key_variables.get('n_bld')
    kv.p_cu = key_variables.get('p_cu')
    kv.t_vnt = key_variables.get('t_vnt')
    kv.f_pd = key_variables.get('f_pd')
    kv.m_ip = key_variables.get('m_ip')
    if calibration:
        kv.alpha = calibration.get('alpha')
        kv.beta = calibration.get('beta')
        kv.gamma = calibration.get('gamma')
        kv.delta = calibration.get('delta')
        kv.n_tgt = calibration.get('n_tgt')


def _apply_calculation_results(tw, results, key_variables, calibration):
    """Apply calculation result values to a model instance."""
    interim = results.get('interim_output', {})
    output = results.get('output_data', {})
    tw.stage1_dilution = interim.get('stage1_dilution')
    tw.stage2_dilution = interim.get('stage2_dilution')
    tw.total_dilution = interim.get('total_dilution')
    tw.filtration_pct = interim.get('filtration_pct')
    tw.w_dry = output.get('w_dry')
    tw.w_tob = output.get('w_tob')
    tw.w_cig = output.get('w_cig')
    tw.w_ntm = output.get('w_ntm')
    tw.tw = output.get('w_cig')
    tw.input_n_bld = key_variables.get('n_bld')
    tw.input_p_cu = key_variables.get('p_cu')
    tw.input_t_vnt = key_variables.get('t_vnt')
    tw.input_f_pd = key_variables.get('f_pd')
    tw.input_m_ip = key_variables.get('m_ip')
    tw.input_alpha = calibration.get('alpha')
    tw.input_beta = calibration.get('beta')
    tw.input_gamma = calibration.get('gamma')
    tw.input_delta = calibration.get('delta')
    tw.input_n_tgt = calibration.get('n_tgt')


def save_key_variables(process_order_id, key_variables, calibration=None):
    """Save key variables and calibration constants for process order."""
    kv_repo = KeyVariableRepository(g.db)
    kv = ProcessOrderKeyVariable(process_order_id=process_order_id)
    _apply_key_variables(kv, key_variables, calibration)
    kv_repo.create(kv)


def save_calculation_results(process_order_id, results, key_variables, calibration):
    """Save target weight calculation results for process order."""
    tw_repo = TargetWeightResultRepository(g.db)
    tw = TargetWeightResult(process_order_id=process_order_id)
    _apply_calculation_results(tw, results, key_variables, calibration)
    tw_repo.create(tw)


def update_key_variables(process_order_id, key_variables, calibration=None):
    """Update key variables for an existing process order."""
    kv_repo = KeyVariableRepository(g.db)
    existing = kv_repo.get_by_process_order(process_order_id)
    if existing:
        _apply_key_variables(existing, key_variables, calibration)
    else:
        save_key_variables(process_order_id, key_variables, calibration)


def update_calculation_results(process_order_id, results, key_variables, calibration):
    """Update target weight calculation results for an existing process order."""
    tw_repo = TargetWeightResultRepository(g.db)
    existing = tw_repo.get_by_process_order(process_order_id)
    if existing:
        _apply_calculation_results(existing, results, key_variables, calibration)
    else:
        save_calculation_results(process_order_id, results, key_variables, calibration)


@bp.route('/view/<id>')
@require_auth
@require_permission(Permissions.FG_CODE_VIEW)
def view(id):
    """Full Excel-style detail view for a single FG Code."""
    repo = FGCodeRepository(g.db)
    fg = repo.get_by_id(id)
    if not fg:
        from app.utils.errors import NotFoundError
        raise NotFoundError('FG Code', id)
    return render_template('fg_codes/view.html', fg=fg)


# Legacy routes for backward compatibility
@bp.route('/list')
@require_auth
@require_permission(Permissions.FG_CODE_VIEW)
def list_view():
    """Legacy list view - redirect to main interface."""
    return redirect(url_for('fg_codes.index'))


@bp.route('/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.FG_CODE_CREATE)
def create():
    """Create new FG code - admin function."""
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = FGCodeRepository(g.db)

        # Basic validation
        if not data.get('fg_code'):
            flash_error('FG Code is required')
            return render_template('fg_codes/form.html', data=data, errors=[])

        if repo.get_by_code(data['fg_code']):
            flash_error('FG Code already exists')
            return render_template('fg_codes/form.html', data=data, errors=[])

        fg = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'FGCode', entity_id=fg.id, after_value=data, module='fg_codes')
        flash_success(f'FG Code {data["fg_code"]} created')
        return redirect(url_for('fg_codes.index'))

    return render_template('fg_codes/form.html', data={}, errors=[])
