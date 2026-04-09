"""Reports module – generate and download PDF/Excel reports."""
import os
from flask import Blueprint, render_template, request, send_file, g, jsonify, current_app
from app.auth.decorators import require_auth, require_permission, require_any_permissions
from app.config.constants import Permissions, AuditAction
from app.repositories import (
    ReportRepository, ProcessOrderRepository, NPLResultRepository,
    TargetWeightResultRepository, NPLInputRepository, FGCodeRepository,
)
from app.services.report_generator import ReportGenerator
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('reports', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.REPORT_VIEW)
def index():
    page, per_page = paginate_args(request.args)
    repo = ReportRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page)
    return render_template('reports/index.html', **result)


@bp.route('/generate', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.REPORT_GENERATE)
def generate():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        output_format = request.form.get('format', 'pdf')
        process_order_id = request.form.get('process_order_id')

        generator = ReportGenerator(
            output_dir=current_app.config.get('REPORT_OUTPUT_DIR', 'reports'),
            template_dir=current_app.config.get('REPORT_TEMPLATE_DIR', 'app/reports/templates'),
        )

        # Build context based on report type
        context = _build_report_context(report_type, process_order_id)

        if output_format == 'excel':
            headers, data = _flatten_for_excel(report_type, context)
            filepath = generator.generate_excel(data, headers, sheet_name=report_type)
        else:
            template_name = f'{report_type}.html'
            filepath = generator.generate_pdf(template_name, context)

        # Save report record
        report_repo = ReportRepository(g.db)
        report_repo.create({
            'report_type': report_type,
            'format': output_format,
            'file_path': filepath,
            'process_order_id': process_order_id,
        })
        g.db.commit()

        AuditLogger.log(AuditAction.GENERATE_REPORT, 'Report',
                        after={'type': report_type, 'format': output_format},
                        module='reports')
        flash_success('Report generated')
        return send_file(filepath, as_attachment=True)

    po_repo = ProcessOrderRepository(g.db)
    orders = po_repo.get_all()
    try:
        from app.repositories import FGCodeRepository as _FGRepo
        fg_codes = _FGRepo(g.db).get_all()
    except Exception:
        fg_codes = []
    return render_template('reports/generate.html', orders=orders,
                           fg_codes=fg_codes, data={}, errors={})


@bp.route('/download/<id>')
@require_auth
@require_permission(Permissions.REPORT_VIEW)
def download(id):
    repo = ReportRepository(g.db)
    report = repo.get_by_id(id)
    if not report:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Report', id)
    if not os.path.exists(report.file_path):
        from app.utils.errors import NotFoundError
        raise NotFoundError('Report file')
    return send_file(report.file_path, as_attachment=True)


def _build_report_context(report_type: str, process_order_id: str = None) -> dict:
    """Build template context for a given report type."""
    from app.database import get_scoped_session
    session = get_scoped_session()
    context = {'report_type': report_type}

    if process_order_id:
        po_repo = ProcessOrderRepository(session)
        context['process_order'] = po_repo.get_by_id(process_order_id)

        tw_repo = TargetWeightResultRepository(session)
        context['target_weight'] = tw_repo.get_by_process_order(process_order_id)

        npl_repo = NPLResultRepository(session)
        context['npl_result'] = npl_repo.get_by_process_order(process_order_id)

    return context


def _flatten_for_excel(report_type: str, context: dict):
    """Convert report context to flat headers + rows for Excel export."""
    if report_type == 'target_weight':
        tw = context.get('target_weight')
        headers = ['TW (mg)', 'W_DRY', 'W_TOB', 'W_CIG', 'W_NTM',
                    'Stage1 Dilution', 'Stage2 Dilution', 'Total Dilution',
                    'Filtration %', 'Nic Demand S1', 'Nic Demand S2',
                    'Total Nicotine', 'Nic Demand Total']
        if tw:
            data = [[
                tw.tw, tw.w_dry, tw.w_tob, tw.w_cig, tw.w_ntm,
                tw.stage1_dilution, tw.stage2_dilution, tw.total_dilution,
                tw.filtration_pct, tw.stage1_pacifying_nicotine_demand,
                tw.stage2_pacifying_nicotine_demand,
                tw.total_filtration_pct, tw.total_nicotine_demand,
            ]]
        else:
            data = []
        return headers, data

    if report_type == 'npl':
        npl = context.get('npl_result')
        headers = ['NPL %', 'NPL kg', 'TAC', 'TTC', 'Total Waste']
        if npl:
            data = [[npl.npl_pct, npl.npl_kg, npl.tac, npl.ttc, npl.total_waste]]
        else:
            data = []
        return headers, data

    return ['Report'], [['No data']]


@bp.route('/natural-loss')
@require_auth
@require_any_permissions(Permissions.REPORT_VIEW, Permissions.REPORT_GENERATE)
def natural_loss():
    """Natural Loss % reports grouped by Blend GTIN and FG GTIN."""
    po_repo = ProcessOrderRepository(g.db)
    fg_repo = FGCodeRepository(g.db)
    npl_repo = NPLResultRepository(g.db)
    npl_input_repo = NPLInputRepository(g.db)

    all_orders = po_repo.get_all()
    po_ids = [o.id for o in all_orders]

    # Build lookups - bulk fetch to avoid N+1 queries
    fg_ids = list({o.fg_code_id for o in all_orders if o.fg_code_id})
    fg_map = {fg.id: fg for fg in fg_repo.get_by_ids(fg_ids)}

    npl_map = npl_repo.get_by_process_orders(po_ids)
    npl_input_map = npl_input_repo.get_by_process_orders(po_ids)

    # Aggregate by Blend GTIN and FG GTIN
    blend_agg = {}
    fg_agg = {}

    for po in all_orders:
        fg = fg_map.get(po.fg_code_id)
        if not fg:
            continue
        npl_input = npl_input_map.get(po.id)
        npl_result = npl_map.get(po.id)
        if not npl_input or not npl_result:
            continue

        t_usd = float(npl_input.t_usd or 0)
        l_dst = float(npl_input.l_dst or 0)
        npl_kg = float(npl_result.npl_kg or 0)

        # Blend GTIN aggregation
        b_gtin = fg.blend_gtin or '-'
        if b_gtin not in blend_agg:
            blend_agg[b_gtin] = {'t_usd': 0, 'l_dst': 0, 'npl_kg': 0}
        blend_agg[b_gtin]['t_usd'] += t_usd
        blend_agg[b_gtin]['l_dst'] += l_dst
        blend_agg[b_gtin]['npl_kg'] += npl_kg

        # FG GTIN aggregation
        f_gtin = fg.fg_gtin or '-'
        if f_gtin not in fg_agg:
            fg_agg[f_gtin] = {'t_usd': 0, 'l_dst': 0, 'npl_kg': 0}
        fg_agg[f_gtin]['t_usd'] += t_usd
        fg_agg[f_gtin]['l_dst'] += l_dst
        fg_agg[f_gtin]['npl_kg'] += npl_kg

    def _build_rows(agg):
        rows = []
        for gtin, vals in sorted(agg.items()):
            t = vals['t_usd']
            dust_pct = (vals['l_dst'] / t * 100) if t else 0
            moist_pct = (vals['npl_kg'] / t * 100) if t else 0
            rows.append({
                'gtin': gtin,
                't_usd': vals['t_usd'],
                'l_dst': vals['l_dst'],
                'npl_kg': vals['npl_kg'],
                'dust_pct': dust_pct,
                'moist_pct': moist_pct,
            })
        return rows

    blend_rows = _build_rows(blend_agg)
    fg_rows = _build_rows(fg_agg)

    return render_template('reports/natural_loss.html',
                           blend_rows=blend_rows, fg_rows=fg_rows)
