"""Dashboard module – landing page with KPI widgets."""
from flask import Blueprint, render_template, g
from sqlalchemy import func
from app.auth.decorators import require_auth
from app.database import get_scoped_session
from app.models.process_order import ProcessOrder
from app.models.npl import NPLResult
from app.models.audit_log import AuditLog
from app.models.fg_code import FGCode

bp = Blueprint('dashboard', __name__, template_folder='templates')


@bp.route('/')
@require_auth
def index():
    """Main dashboard view with live KPI data."""
    db = g.db or get_scoped_session()

    # Single grouped query for all status counts (reduces N queries to 1)
    active_statuses = ['Draft', 'Calculated', 'QA Pending', 'QA Updated']
    status_rows = (
        db.query(ProcessOrder.status, func.count(ProcessOrder.id))
        .filter(ProcessOrder.is_deleted == False)  # noqa: E712
        .group_by(ProcessOrder.status)
        .all()
    )
    status_counts = {}
    total_orders = 0
    active_orders = 0
    completed_orders = 0
    for status, cnt in status_rows:
        status_counts[status] = cnt
        total_orders += cnt
        if status in active_statuses:
            active_orders += cnt
        if status == 'Completed':
            completed_orders = cnt

    # Ensure all expected statuses exist in dict
    for s in ['Draft', 'Calculated', 'QA Pending', 'QA Updated', 'Completed', 'Report Generated']:
        status_counts.setdefault(s, 0)

    # KPI: pending QA + average NPL in single combined query scope
    from app.models.qa import QAAnalysis
    pending_qa = (
        db.query(func.count(QAAnalysis.id))
        .filter(QAAnalysis.status == 'Pending')
        .scalar()
    ) or 0

    avg_npl_row = db.query(func.avg(NPLResult.npl_pct)).scalar()
    avg_npl = round(avg_npl_row, 2) if avg_npl_row is not None else None

    # Recent process orders (last 10)
    recent_orders = (
        db.query(ProcessOrder, FGCode.fg_code)
        .outerjoin(FGCode, ProcessOrder.fg_code_id == FGCode.id)
        .filter(ProcessOrder.is_deleted == False)  # noqa: E712
        .order_by(ProcessOrder.process_date.desc())
        .limit(10)
        .all()
    )

    # Recent audit activity (last 8)
    recent_activity = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(8)
        .all()
    )

    return render_template(
        'dashboard/index.html',
        total_orders=total_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        pending_qa=pending_qa,
        avg_npl=avg_npl,
        recent_orders=recent_orders,
        recent_activity=recent_activity,
        status_counts=status_counts,
    )
