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

    # Get latest key variables and target weight
    kv_repo = KeyVariableRepository(g.db)
    kvs = kv_repo.get_all(filters={'process_order_id': process_order_id})
    kv = kvs[-1] if kvs else None

    # Get tolerance limits
    limit_repo = OptimizerLimitRepository(g.db)
    limits = limit_repo.get_limits_for_fg(po.fg_code_id)
    limits_dict = {}
    for lim in limits:
        limits_dict[lim.parameter_name] = {
            'lower': float(lim.lower_limit) if lim.lower_limit else None,
            'upper': float(lim.upper_limit) if lim.upper_limit else None,
        }

    if request.method == 'POST':
        data = request.form.to_dict()
        method = data.get('method', 'adjustment')

        # Validate
        engine = optimizer_input_engine(limits_dict)
        data['process_order_id'] = process_order_id
        result = engine.validate(data)
        if not result.is_valid:
            flash_error('Validation failed')
            return render_template('optimizer/run.html',
                                   po=po, kv=kv, limits=limits_dict,
                                   data=data, errors=result.errors)

        # Build base values from key variables
        base_values = {}
        if kv:
            base_values = {
                'n_bld': float(kv.n_bld or 0),
                'p_cu': float(kv.p_cu or 0),
                't_vnt': float(kv.t_vnt or 0),
                'f_pd': float(kv.f_pd or 0),
                'm_ip': float(kv.m_ip or 0),
            }

        # Parse adjustments/values from form
        adjustments = {}
        manual_values = {}
        param_keys = ['n_bld', 'p_cu', 't_vnt', 'f_pd', 'm_ip']
        for key in param_keys:
            val = data.get(f'{method}_{key}')
            if val:
                if method == 'adjustment':
                    adjustments[key] = float(val)
                elif method == 'manual':
                    manual_values[key] = float(val)

        # Run optimizer
        config = OptimizerConfig(limits=limits_dict)
        optimizer = ProductRunOptimizer(config)
        opt_input = OptInput(
            method=method,
            base_values=base_values,
            adjustments=adjustments,
            manual_values=manual_values,
            direct_values={k: float(v) for k, v in data.items() if k.startswith('direct_')},
        )
        opt_result = optimizer.optimize(opt_input)

        # Save optimizer run
        run_repo = OptimizerRunRepository(g.db)
        opt_run = run_repo.create({
            'process_order_id': process_order_id,
            'method': method,
            'is_verified': opt_result.within_tolerance,
        })

        # Save optimizer input
        input_repo = OptimizerInputRepository(g.db)
        input_repo.create({
            'optimizer_run_id': opt_run.id,
            **{f'base_{k}': v for k, v in base_values.items()},
            **{f'adj_{k}': v for k, v in adjustments.items()},
            **{f'manual_{k}': v for k, v in manual_values.items()},
        })

        # Save optimizer result
        result_repo = OptimizerResultRepository(g.db)
        result_repo.create({
            'optimizer_run_id': opt_run.id,
            **{f'opt_{k}': v for k, v in opt_result.optimized_values.items()},
            'within_tolerance': opt_result.within_tolerance,
        })
        g.db.commit()

        AuditLogger.log(AuditAction.OPTIMIZE, 'Optimizer',
                        entity_id=opt_run.id,
                        after={'method': method, 'within_tolerance': opt_result.within_tolerance},
                        module='optimizer')
        flash_success('Optimization completed')
        return render_template('optimizer/result.html',
                               po=po, opt_result=opt_result, method=method)

    return render_template('optimizer/run.html',
                           po=po, kv=kv, limits=limits_dict, data={}, errors=[])
