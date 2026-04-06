"""Batch Processing module – submit and track batch jobs."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions, AuditAction, BatchJobStatus, BatchJobType
from app.repositories import (
    BatchJobRepository, BatchJobItemRepository, ProcessOrderRepository,
)
from app.services.batch_processor import BatchProcessor
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger

bp = Blueprint('batch', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.BATCH_VIEW)
def index():
    page, per_page = paginate_args(request.args)
    repo = BatchJobRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page)
    active_jobs = BatchProcessor.get_active_jobs()
    return render_template('batch/index.html', active_jobs=active_jobs, **result)


@bp.route('/submit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.BATCH_SUBMIT)
def submit():
    if request.method == 'POST':
        data = request.form.to_dict()
        job_type = data.get('job_type')
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        # Create batch job record
        job_repo = BatchJobRepository(g.db)
        job = job_repo.create({
            'job_type': job_type,
            'status': BatchJobStatus.PENDING.value,
            'date_range_from': date_from,
            'date_range_to': date_to,
        })

        # Find process orders in range and create batch items
        po_repo = ProcessOrderRepository(g.db)
        orders = po_repo.get_all()  # Will filter by date range
        item_repo = BatchJobItemRepository(g.db)
        for po in orders:
            item_repo.create({
                'batch_job_id': job.id,
                'entity_type': 'ProcessOrder',
                'entity_id': po.id,
                'status': 'pending',
            })
        job.total_count = len(orders)
        g.db.commit()

        # Define processor function based on job type
        def process_item(item, session):
            from app.services.target_weight_calc import TargetWeightCalculator
            # Processing logic depends on job_type
            pass

        # Submit to batch processor
        from flask import current_app
        processor = BatchProcessor(
            max_workers=current_app.config.get('BATCH_WORKER_THREADS', 3),
            chunk_size=current_app.config.get('BATCH_CHUNK_SIZE', 50),
            max_retries=current_app.config.get('BATCH_RETRY_MAX', 3),
        )
        processor.submit_job(job.id, process_item)

        AuditLogger.log(AuditAction.CREATE, 'BatchJob',
                        entity_id=job.id, after={'job_type': job_type}, module='batch')
        flash_success(f'Batch job submitted ({len(orders)} items)')
        return redirect(url_for('batch.detail', id=job.id))

    job_types = [t.value for t in BatchJobType]
    fg_repo = FGCodeRepository(g.db) if 'FGCodeRepository' in dir() else None
    fg_codes = []
    try:
        from app.repositories import FGCodeRepository as _FGRepo
        fg_codes = _FGRepo(g.db).get_all()
    except Exception:
        pass
    return render_template('batch/submit.html', job_types=job_types,
                           fg_codes=fg_codes, data={}, errors={})


@bp.route('/<id>')
@require_auth
@require_permission(Permissions.BATCH_VIEW)
def detail(id):
    repo = BatchJobRepository(g.db)
    job = repo.get_by_id(id)
    if not job:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Batch Job', id)
    item_repo = BatchJobItemRepository(g.db)
    items = item_repo.get_all(filters={'batch_job_id': id})
    return render_template('batch/detail.html', job=job, items=items)


@bp.route('/<id>/status')
@require_auth
@require_permission(Permissions.BATCH_VIEW)
def status(id):
    """HTMX endpoint – returns job progress fragment."""
    repo = BatchJobRepository(g.db)
    job = repo.get_by_id(id)
    if not job:
        return jsonify({'error': 'not found'}), 404
    return jsonify({
        'status': job.status,
        'total': job.total_count,
        'processed': job.processed_count,
        'failed': job.failed_count,
        'progress': round(job.processed_count / job.total_count * 100) if job.total_count else 0,
    })
