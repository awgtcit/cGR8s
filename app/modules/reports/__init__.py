"""Reports module – generate and download PDF/Excel reports."""
import os
from flask import Blueprint, render_template, request, send_file, g, jsonify, current_app
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction
from app.repositories import (
    ReportRepository, ProcessOrderRepository, NPLResultRepository,
    TargetWeightResultRepository,
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
                    'Nic Demand Total', 'Total Nicotine']
        if tw:
            data = [[
                tw.tw, tw.w_dry, tw.w_tob, tw.w_cig, tw.w_ntm,
                tw.stage1_dilution, tw.stage2_dilution, tw.total_dilution,
                tw.filtration_pct, tw.stage1_pacifying_nicotine_demand,
                tw.stage2_pacifying_nicotine_demand,
                tw.total_nicotine_demand, tw.total_filtration_pct,
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
