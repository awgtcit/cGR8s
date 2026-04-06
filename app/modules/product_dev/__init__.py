"""Product Development module — manage product development requests."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission
from app.config.constants import Permissions

bp = Blueprint('product_dev', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.PRODUCT_DEV_VIEW)
def index():
    """List product development requests."""
    return render_template('product_dev/index.html')


@bp.route('/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.PRODUCT_DEV_CREATE)
def create():
    """Create a new product development request."""
    if request.method == 'POST':
        # TODO: wire to ProductDevRepository
        return redirect(url_for('product_dev.index'))
    return render_template('product_dev/form.html', data={}, errors=[])


@bp.route('/<id>')
@require_auth
@require_permission(Permissions.PRODUCT_DEV_VIEW)
def detail(id):
    """View a product development request."""
    return render_template('product_dev/detail.html', item_id=id)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.PRODUCT_DEV_UPDATE)
def edit(id):
    """Edit a product development request."""
    if request.method == 'POST':
        # TODO: wire to ProductDevRepository
        return redirect(url_for('product_dev.detail', id=id))
    return render_template('product_dev/form.html', data={}, errors=[], edit=True)


@bp.route('/<id>/approve', methods=['POST'])
@require_auth
@require_permission(Permissions.PRODUCT_DEV_APPROVE)
def approve(id):
    """Approve a product development request."""
    # TODO: wire to ProductDevRepository
    return jsonify({'success': True, 'message': 'Approved'})
