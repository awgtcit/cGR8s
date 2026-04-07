"""Process Orders module – create, manage, and track process orders."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction, ProcessOrderStatus
from app.repositories import (
    ProcessOrderRepository, FGCodeRepository,
    TargetWeightResultRepository, NPLResultRepository,
)
from app.rules.validators import process_order_create_engine, process_order_status_engine
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('process_orders', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.PROCESS_ORDER_VIEW)
def index():
    page, per_page = paginate_args(request.args)
    repo = ProcessOrderRepository(g.db)
    search = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    filters = {}
    if status_filter:
        filters['status'] = status_filter
    result = repo.get_paginated(
        page=page, per_page=per_page,
        search=search,
        search_fields=['process_order_number'],
        filters=filters,
    )
    statuses = [s.value for s in ProcessOrderStatus]
    # Build FG code lookup for display (single bulk query)
    fg_repo = FGCodeRepository(g.db)
    fg_code_ids = list({po.fg_code_id for po in result.get('items', []) if po.fg_code_id})
    fg_lookup = fg_repo.get_fg_code_map(fg_code_ids)
    blend_lookup = fg_repo.get_fg_blend_map(fg_code_ids)

    # Build workflow status per PO (TW done? NPL done?) — bulk queries
    from app.models.target_weight_result import TargetWeightResult
    from app.models.npl import NPLResult
    po_ids = [po.id for po in result.get('items', [])]
    tw_done = set()
    npl_done = set()
    tw_values = {}
    if po_ids:
        tw_rows = g.db.query(
            TargetWeightResult.process_order_id, TargetWeightResult.w_cig
        ).filter(TargetWeightResult.process_order_id.in_(po_ids)).all()
        for row in tw_rows:
            tw_done.add(row.process_order_id)
            tw_values[row.process_order_id] = row.w_cig

        npl_rows = g.db.query(
            NPLResult.process_order_id
        ).filter(NPLResult.process_order_id.in_(po_ids)).distinct().all()
        for row in npl_rows:
            npl_done.add(row.process_order_id)

    return render_template('process_orders/index.html',
                           search=search, status_filter=status_filter,
                           statuses=statuses, fg_lookup=fg_lookup,
                           tw_done=tw_done, npl_done=npl_done,
                           tw_values=tw_values, blend_lookup=blend_lookup,
                           **result)


@bp.route('/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.PROCESS_ORDER_CREATE)
def create():
    fg_repo = FGCodeRepository(g.db)
    fg_codes = fg_repo.get_all()

    if request.method == 'POST':
        data = request.form.to_dict()
        repo = ProcessOrderRepository(g.db)
        engine = process_order_create_engine(repo)
        result = engine.validate(data)
        if not result.is_valid:
            flash_error('Validation failed')
            return render_template('process_orders/form.html',
                                   data=data, errors=result.errors, fg_codes=fg_codes)
        data['status'] = ProcessOrderStatus.DRAFT.value
        po = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'ProcessOrder',
                        entity_id=po.id, after_value=data, module='process_orders')
        flash_success(f'Process Order {data["process_order_number"]} created')
        return redirect(url_for('process_orders.detail', id=po.id))

    return render_template('process_orders/form.html',
                           data={}, errors=[], fg_codes=fg_codes)


@bp.route('/<id>')
@require_auth
@require_permission(Permissions.PROCESS_ORDER_VIEW)
def detail(id):
    repo = ProcessOrderRepository(g.db)
    po = repo.get_by_id(id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', id)
    fg_repo = FGCodeRepository(g.db)
    fg = fg_repo.get_by_id(po.fg_code_id) if po.fg_code_id else None

    # Get workflow results for this PO
    tw_repo = TargetWeightResultRepository(g.db)
    npl_repo = NPLResultRepository(g.db)
    tw = tw_repo.get_by_process_order(id)
    npl = npl_repo.get_by_process_order(id)

    return render_template('process_orders/detail.html', po=po, fg=fg,
                           tw=tw, npl=npl)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.PROCESS_ORDER_EDIT)
def edit(id):
    repo = ProcessOrderRepository(g.db)
    po = repo.get_by_id(id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', id)
    fg_repo = FGCodeRepository(g.db)
    fg_codes = fg_repo.get_all()

    if request.method == 'POST':
        data = request.form.to_dict()
        before = {c.name: getattr(po, c.name) for c in po.__table__.columns}
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'ProcessOrder',
                        entity_id=id, before_value=before, after_value=data, module='process_orders')
        flash_success('Process Order updated')
        return redirect(url_for('process_orders.detail', id=id))

    data = {c.name: getattr(po, c.name) for c in po.__table__.columns}
    return render_template('process_orders/form.html',
                           data=data, errors=[], fg_codes=fg_codes, po=po)


@bp.route('/<id>/status', methods=['POST'])
@require_auth
@require_permission(Permissions.PROCESS_ORDER_EDIT)
def change_status(id):
    repo = ProcessOrderRepository(g.db)
    po = repo.get_by_id(id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', id)

    target_status = request.form.get('status')
    engine = process_order_status_engine()
    result = engine.validate({
        'current_status': po.status,
        'target_status': target_status,
    })
    if not result.is_valid:
        flash_error(result.errors[0].message)
        return redirect(url_for('process_orders.detail', id=id))

    repo.update(id, {'status': target_status})
    g.db.commit()
    AuditLogger.log(AuditAction.STATUS_CHANGE, 'ProcessOrder',
                    entity_id=id, before_value={'status': po.status},
                    after_value={'status': target_status}, module='process_orders')
    flash_success(f'Status changed to {target_status}')
    return redirect(url_for('process_orders.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.PROCESS_ORDER_DELETE)
def delete(id):
    repo = ProcessOrderRepository(g.db)
    po = repo.get_by_id(id)
    if not po:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Process Order', id)

    # Cascade-delete all child records (order matters for FK constraints)
    from app.models.qa import QAAnalysis, QAUpdate
    from app.models.optimizer import OptimizerRun, OptimizerInput, OptimizerResult
    from app.models.npl import NPLInput, NPLResult
    from app.models.target_weight_result import TargetWeightResult
    from app.models.key_variable import ProcessOrderKeyVariable
    from app.models.report import Report

    try:
        # 1. QAUpdate (child of QAAnalysis)
        qa_ids = [r.id for r in g.db.query(QAAnalysis.id).filter(
            QAAnalysis.process_order_id == id).all()]
        if qa_ids:
            g.db.query(QAUpdate).filter(QAUpdate.qa_analysis_id.in_(qa_ids)).delete(
                synchronize_session=False)

        # 2. QAAnalysis
        g.db.query(QAAnalysis).filter(
            QAAnalysis.process_order_id == id).delete(synchronize_session=False)

        # 3. OptimizerInput / OptimizerResult (children of OptimizerRun)
        opt_ids = [r.id for r in g.db.query(OptimizerRun.id).filter(
            OptimizerRun.process_order_id == id).all()]
        if opt_ids:
            g.db.query(OptimizerResult).filter(
                OptimizerResult.optimizer_run_id.in_(opt_ids)).delete(
                synchronize_session=False)
            g.db.query(OptimizerInput).filter(
                OptimizerInput.optimizer_run_id.in_(opt_ids)).delete(
                synchronize_session=False)

        # 4. OptimizerRun
        g.db.query(OptimizerRun).filter(
            OptimizerRun.process_order_id == id).delete(synchronize_session=False)

        # 5. NPLResult
        g.db.query(NPLResult).filter(
            NPLResult.process_order_id == id).delete(synchronize_session=False)

        # 6. NPLInput
        g.db.query(NPLInput).filter(
            NPLInput.process_order_id == id).delete(synchronize_session=False)

        # 7. TargetWeightResult
        g.db.query(TargetWeightResult).filter(
            TargetWeightResult.process_order_id == id).delete(synchronize_session=False)

        # 8. ProcessOrderKeyVariable
        g.db.query(ProcessOrderKeyVariable).filter(
            ProcessOrderKeyVariable.process_order_id == id).delete(
            synchronize_session=False)

        # 9. Reports
        g.db.query(Report).filter(
            Report.process_order_id == id).delete(synchronize_session=False)

        # 10. Soft-delete ProcessOrder
        repo.soft_delete(id, user_id=getattr(g, 'user_id', None))
        g.db.commit()
    except Exception:
        g.db.rollback()
        flash_error('Failed to delete Process Order – please try again')
        return redirect(url_for('process_orders.detail', id=id))

    AuditLogger.log(AuditAction.DELETE, 'ProcessOrder', entity_id=id,
                    after_value={'cascade': True,
                                 'process_order_number': po.process_order_number},
                    module='process_orders')
    flash_success(f'Process Order {po.process_order_number} and all related data deleted')
    return redirect(url_for('process_orders.index'))
