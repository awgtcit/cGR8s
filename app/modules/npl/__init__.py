"""NPL (Non-Product Losses) Calculation module."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction
from app.repositories import (
    ProcessOrderRepository, NPLInputRepository, NPLResultRepository,
    TargetWeightResultRepository, KeyVariableRepository, FGCodeRepository,
)
from app.models.npl import NPLInput as NPLInputModel, NPLResult as NPLResultModel
from app.services.npl_calc import NPLCalculator, NPLInput
from app.rules.validators import npl_input_engine
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('npl', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.NPL_VIEW)
def index():
    page, per_page = paginate_args(request.args)
    repo = NPLResultRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page)
    # Build PO number lookup for display (single bulk query)
    po_repo = ProcessOrderRepository(g.db)
    po_ids = list({r.process_order_id for r in result.get('items', []) if r.process_order_id})
    po_lookup = po_repo.get_po_number_map(po_ids)
    return render_template('npl/index.html', po_lookup=po_lookup, **result)


@bp.route('/calculate/<process_order_id>', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.NPL_CALCULATE)
def calculate(process_order_id):
    po_repo = ProcessOrderRepository(g.db)
    po = po_repo.get_by_id(process_order_id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', process_order_id)

    # Get target weight result for this PO
    tw_repo = TargetWeightResultRepository(g.db)
    tw_results = tw_repo.get_all(filters={'process_order_id': process_order_id})
    tw = tw_results[-1] if tw_results else None

    # Get key variables (calibration constants snapshot)
    kv_repo = KeyVariableRepository(g.db)
    kv = kv_repo.get_by_process_order(process_order_id)

    # Get FG code for c_plg
    fg_repo = FGCodeRepository(g.db)
    fg = fg_repo.get_by_id(po.fg_code_id) if po.fg_code_id else None

    # Get existing NPL input/result for this PO (for update-not-duplicate)
    npl_in_repo = NPLInputRepository(g.db)
    npl_res_repo = NPLResultRepository(g.db)
    existing_input = npl_in_repo.get_by_process_order(process_order_id)
    existing_result = npl_res_repo.get_by_process_order(process_order_id)

    # Build reference data for template
    ref = {
        'n_bld': float(kv.n_bld or 0) if kv else 0,
        'p_cu': float(kv.p_cu or 0) if kv else 0,
        't_vnt': float(kv.t_vnt or 0) if kv else 0,
        'f_pd': float(kv.f_pd or 0) if kv else 0,
        'm_ip': float(kv.m_ip or 0) if kv else 0,
        'alpha': float(kv.alpha or 0) if kv else 0,
        'beta': float(kv.beta or 0) if kv else 0,
        'gamma': float(kv.gamma or 0) if kv else 0,
        'delta': float(kv.delta or 0) if kv else 0,
        'n_tgt': float(kv.n_tgt or 0) if kv else 0,
        'c_plg': int(fg.c_plg or 1) if fg and fg.c_plg else 1,
        'w_tob': float(tw.w_tob or 0) if tw else 0,
        'w_ntm': float(tw.w_ntm or 0) if tw else 0,
        'w_cig': float(tw.w_cig or 0) if tw else 0,
    }

    if request.method == 'POST':
        data = request.form.to_dict()
        data['process_order_id'] = process_order_id

        # Normalize empty numeric fields to '0' before validation
        numeric_fields = [
            't_iss', 't_un', 'l_dst', 'l_win', 'l_flr', 'l_srt', 'l_dt',
            'n_mc', 'n_cg', 'r_mkg', 'r_ndt', 'r_pkg', 'm_dsp', 'm_dst',
            'n_w',
        ]
        for nf in numeric_fields:
            if not data.get(nf, '').strip():
                data[nf] = '0'

        engine = npl_input_engine()
        result = engine.validate(data)
        if not result.is_valid:
            flash_error('Validation failed')
            return render_template('npl/calculate.html',
                                   po=po, fg=fg, tw=tw, ref=ref, data=data,
                                   errors=result.errors, npl_result=existing_result)

        # Parse NPL form inputs (empty → 0)
        def fval(key):
            v = data.get(key, '').strip()
            return float(v) if v else 0

        npl_form = {
            't_iss': fval('t_iss'),
            't_un': fval('t_un'),
            'l_dst': fval('l_dst'),
            'l_win': fval('l_win'),
            'l_flr': fval('l_flr'),
            'l_srt': fval('l_srt'),
            'l_dt': fval('l_dt'),
            'n_mc': fval('n_mc'),
            'n_cg': fval('n_cg'),
            'r_mkg': fval('r_mkg'),
            'r_ndt': fval('r_ndt'),
            'r_pkg': fval('r_pkg'),
            'm_dsp': fval('m_dsp'),
            'm_dst': fval('m_dst'),
            'n_w': fval('n_w'),
            't_usd': (fval('l_dst') - fval('t_iss')) / 1_000_000,
        }

        # Update existing or create new NPL input
        if existing_input:
            for k, v in npl_form.items():
                setattr(existing_input, k, v)
            npl_in_repo.update(existing_input)
            npl_input_entity = existing_input
        else:
            npl_input_entity = NPLInputModel(
                process_order_id=process_order_id,
                **{k: v for k, v in npl_form.items()},
            )
            npl_in_repo.create(npl_input_entity)

        # Build calculator input (exclude t_usd – calculator computes it)
        calc_form = {k: v for k, v in npl_form.items() if k != 't_usd'}
        npl_input = NPLInput(
            # Form inputs
            **calc_form,
            # Key variables from TW
            n_bld=ref['n_bld'],
            p_cu=ref['p_cu'],
            t_vnt=ref['t_vnt'],
            f_pd=ref['f_pd'],
            m_ip=ref['m_ip'],
            # Calibration constants
            alpha=ref['alpha'],
            beta=ref['beta'],
            gamma_val=ref['gamma'],
            delta=ref['delta'],
            n_tgt=ref['n_tgt'],
            # FG info
            n_c=ref['c_plg'],
            w_tob=ref['w_tob'],
        )
        calc = NPLCalculator()
        npl_result = calc.calculate(npl_input)

        # Update existing or create new NPL result
        if existing_result:
            existing_result.npl_input_id = npl_input_entity.id
            existing_result.npl_pct = npl_result.npl_pct
            existing_result.npl_kg = npl_result.npl_kg
            existing_result.tac = npl_result.tac
            existing_result.ttc = npl_result.ttc
            existing_result.tobacco_consumed = npl_result.actual_consumption
            existing_result.theoretical_consumption = npl_result.theoretical_consumption
            existing_result.actual_consumption = npl_result.actual_consumption
            existing_result.verified = False
            npl_res_repo.update(existing_result)
        else:
            npl_result_entity = NPLResultModel(
                process_order_id=process_order_id,
                npl_input_id=npl_input_entity.id,
                npl_pct=npl_result.npl_pct,
                npl_kg=npl_result.npl_kg,
                tac=npl_result.tac,
                ttc=npl_result.ttc,
                tobacco_consumed=npl_result.actual_consumption,
                theoretical_consumption=npl_result.theoretical_consumption,
                actual_consumption=npl_result.actual_consumption,
                verified=False,
            )
            npl_res_repo.create(npl_result_entity)
        g.db.commit()

        result_data = {
            'npl_pct': npl_result.npl_pct,
            'npl_kg': npl_result.npl_kg,
            'tac': npl_result.tac,
            'ttc': npl_result.ttc,
        }
        AuditLogger.log(AuditAction.CALCULATE, 'NPL',
                        entity_id=process_order_id, after_value=result_data, module='npl')
        flash_success('NPL calculated successfully')
        return render_template('npl/result.html', po=po, fg=fg, result=npl_result,
                               input_data=npl_form, ref=ref,
                               process_order_id=process_order_id)

    # GET: pre-fill from existing input or use defaults
    if existing_input:
        data = {
            't_iss': str(existing_input.t_iss or ''),
            't_un': str(existing_input.t_un or ''),
            'l_dst': str(existing_input.l_dst or ''),
            'l_win': str(existing_input.l_win or ''),
            'l_flr': str(existing_input.l_flr or ''),
            'l_srt': str(existing_input.l_srt or ''),
            'l_dt': str(existing_input.l_dt or ''),
            'n_mc': str(existing_input.n_mc or ''),
            'n_cg': str(existing_input.n_cg or ''),
            'r_mkg': str(existing_input.r_mkg or ''),
            'r_ndt': str(existing_input.r_ndt or ''),
            'r_pkg': str(existing_input.r_pkg or ''),
            'm_dsp': str(existing_input.m_dsp or ''),
            'm_dst': str(existing_input.m_dst or ''),
            'n_w': str(existing_input.n_w or ''),
        }
    else:
        data = {
            't_iss': '', 't_un': '',
            'l_dst': '', 'l_win': '', 'l_flr': '', 'l_srt': '', 'l_dt': '',
            'n_mc': '', 'n_cg': '',
            'r_mkg': '', 'r_ndt': '', 'r_pkg': '',
            'm_dsp': '', 'm_dst': '9',
            'n_w': '0',
        }
    return render_template('npl/calculate.html',
                           po=po, fg=fg, tw=tw, ref=ref, data=data,
                           errors=[], npl_result=existing_result)


@bp.route('/verify/<process_order_id>', methods=['POST'])
@require_auth
@require_permission(Permissions.NPL_CALCULATE)
def verify(process_order_id):
    """Verify NPL result and transition PO status Draft → Calculated."""
    po_repo = ProcessOrderRepository(g.db)
    po = po_repo.get_by_id(process_order_id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', process_order_id)

    npl_res_repo = NPLResultRepository(g.db)
    npl_result = npl_res_repo.get_by_process_order(process_order_id)
    if not npl_result:
        flash_error('No NPL result to verify')
        return redirect(url_for('npl.index'))

    npl_result.verified = True

    # Transition PO status: Draft → Calculated
    from app.config.constants import ProcessOrderStatus
    if po.status == ProcessOrderStatus.DRAFT.value:
        po.status = ProcessOrderStatus.CALCULATED.value

    g.db.commit()

    AuditLogger.log(AuditAction.UPDATE, 'NPL',
                    entity_id=process_order_id,
                    after_value={'verified': True, 'status': po.status},
                    module='npl')

    # Return JSON for AJAX requests, redirect otherwise
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'NPL saved successfully'})
    flash_success('NPL result verified and confirmed')
    return redirect(url_for('qa.data_grid'))
