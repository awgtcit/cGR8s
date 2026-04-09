"""Master Data module – Blends, Physical Parameters, Calibration Constants, Machines, SKUs, Targets & Limits."""
from flask import Blueprint, render_template, request, redirect, url_for, g, jsonify
from app.auth.decorators import require_auth, require_permission, require_any_permissions
from app.config.constants import Permissions
from app.repositories import (
    BlendMasterRepository, PhysicalParameterRepository,
    CalibrationConstantRepository, FormulaConstantRepository,
    GammaConstantRepository, LookupRepository, FGCodeRepository,
    MachineRepository, SKURepository, TobaccoBlendAnalysisRepository,
)
from app.utils.helpers import paginate_args, flash_success, flash_error
from app.audit import AuditLogger
from app.config.constants import AuditAction

bp = Blueprint('master_data', __name__, template_folder='templates')


@bp.route('/')
@require_auth
@require_permission(Permissions.MASTER_DATA_VIEW)
def index():
    """Master Data root – redirect to blends."""
    return redirect(url_for('master_data.blends'))


# ── Blend Master ──────────────────────────────────────────────────────────

@bp.route('/blends')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_BLENDS)
def blends():
    page, per_page = paginate_args(request.args)
    repo = BlendMasterRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['blend_code', 'blend_name'])
    return render_template('master_data/blends.html', **result)


@bp.route('/blends/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def blend_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = BlendMasterRepository(g.db)
        blend = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'BlendMaster', entity_id=blend.id, after_value=data, module='master_data')
        flash_success('Blend created')
        return redirect(url_for('master_data.blends'))
    return render_template('master_data/blend_form.html', data={}, errors=[])


@bp.route('/blends/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def blend_edit(id):
    repo = BlendMasterRepository(g.db)
    blend = repo.get_by_id(id)
    if not blend:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Blend', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'BlendMaster', entity_id=id, after_value=data, module='master_data')
        flash_success('Blend updated')
        return redirect(url_for('master_data.blends'))
    data = {c.name: getattr(blend, c.name) for c in blend.__table__.columns}
    return render_template('master_data/blend_form.html', data=data, errors=[], blend=blend)


# ── Physical Parameters ──────────────────────────────────────────────────

@bp.route('/physical-params')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_BLENDS)
def physical_params():
    page, per_page = paginate_args(request.args)
    repo = PhysicalParameterRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page)
    return render_template('master_data/physical_params.html', **result)


@bp.route('/physical-params/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def physical_param_edit(id):
    repo = PhysicalParameterRepository(g.db)
    param = repo.get_by_id(id)
    if not param:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Physical Parameter', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'PhysicalParameter', entity_id=id, after_value=data, module='master_data')
        flash_success('Physical parameter updated')
        return redirect(url_for('master_data.physical_params'))
    data = {c.name: getattr(param, c.name) for c in param.__table__.columns}
    fg_codes = FGCodeRepository(g.db).get_all()
    return render_template('master_data/physical_param_form.html', data=data, param=param, fg_codes=fg_codes, errors={})


# ── Calibration Constants ────────────────────────────────────────────────

@bp.route('/calibration')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_CALIBRATION)
def calibration():
    page, per_page = paginate_args(request.args)
    repo = CalibrationConstantRepository(g.db)
    result = repo.get_paginated_with_fg_search(
        page=page, per_page=per_page,
        search=request.args.get('q', '')
    )
    return render_template('master_data/calibration.html', **result)


@bp.route('/calibration/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def calibration_edit(id):
    repo = CalibrationConstantRepository(g.db)
    cal = repo.get_by_id(id)
    if not cal:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Calibration Constant', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))

        # Sync n_tgt → SKU.nicotine
        if 'n_tgt' in data and cal.fg_code_id:
            try:
                n_tgt_val = float(data['n_tgt']) if data['n_tgt'] else None
            except (ValueError, TypeError):
                n_tgt_val = None
            if n_tgt_val is not None:
                from app.services.nicotine_sync import sync_nicotine
                sync_nicotine(fg_code_id=cal.fg_code_id, n_tgt_val=n_tgt_val)

        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'CalibrationConstant', entity_id=id, after_value=data, module='master_data')
        flash_success('Calibration constant updated')
        return redirect(url_for('master_data.calibration'))
    data = {c.name: getattr(cal, c.name) for c in cal.__table__.columns}
    fg_codes = FGCodeRepository(g.db).get_all()
    return render_template('master_data/calibration_form.html', data=data, constant=cal, fg_codes=fg_codes, errors={})


@bp.route('/calibration/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def calibration_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = CalibrationConstantRepository(g.db)
        cal = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'CalibrationConstant', entity_id=cal.id, after_value=data, module='master_data')
        flash_success('Calibration constant created')
        return redirect(url_for('master_data.calibration'))
    fg_codes = FGCodeRepository(g.db).get_all()
    return render_template('master_data/calibration_form.html', data={}, errors={}, constant=None, fg_codes=fg_codes)


@bp.route('/calibration/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def calibration_delete(id):
    repo = CalibrationConstantRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'CalibrationConstant', entity_id=id, module='master_data')
    flash_success('Calibration constant deleted')
    return redirect(url_for('master_data.calibration'))


@bp.route('/blends/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def blend_delete(id):
    repo = BlendMasterRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'BlendMaster', entity_id=id, module='master_data')
    flash_success('Blend deleted')
    return redirect(url_for('master_data.blends'))


@bp.route('/physical-params/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def physical_param_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = PhysicalParameterRepository(g.db)
        param = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'PhysicalParameter', entity_id=param.id, after_value=data, module='master_data')
        flash_success('Physical parameter created')
        return redirect(url_for('master_data.physical_params'))
    fg_codes = FGCodeRepository(g.db).get_all()
    return render_template('master_data/physical_param_form.html', data={}, errors={}, param=None, fg_codes=fg_codes)


@bp.route('/physical-params/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def physical_param_delete(id):
    repo = PhysicalParameterRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'PhysicalParameter', entity_id=id, module='master_data')
    flash_success('Physical parameter deleted')
    return redirect(url_for('master_data.physical_params'))


# ── Lookups ──────────────────────────────────────────────────────────────

@bp.route('/lookups')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_LOOKUPS)
def lookups():
    repo = LookupRepository(g.db)
    page, per_page = paginate_args(request.args)
    category = request.args.get('category', '')
    result = repo.get_paginated(page=page, per_page=per_page, search=request.args.get('q', ''), search_fields=['code', 'display_name'])
    categories = [r[0] for r in repo.session.query(repo.model_class.category).distinct().all()]
    return render_template('master_data/lookups.html', categories=categories, **result)


@bp.route('/lookups/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def lookup_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = LookupRepository(g.db)
        lk = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'Lookup', entity_id=lk.id, after_value=data, module='master_data')
        flash_success('Lookup created')
        return redirect(url_for('master_data.lookups'))
    return render_template('master_data/lookup_form.html', data={}, errors={}, lookup=None)


@bp.route('/lookups/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def lookup_edit(id):
    repo = LookupRepository(g.db)
    lk = repo.get_by_id(id)
    if not lk:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Lookup', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'Lookup', entity_id=id, after_value=data, module='master_data')
        flash_success('Lookup updated')
        return redirect(url_for('master_data.lookups'))
    data = {c.name: getattr(lk, c.name) for c in lk.__table__.columns}
    return render_template('master_data/lookup_form.html', data=data, lookup=lk, errors={})


@bp.route('/lookups/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def lookup_delete(id):
    repo = LookupRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'Lookup', entity_id=id, module='master_data')
    flash_success('Lookup deleted')
    return redirect(url_for('master_data.lookups'))


# ── Machines ─────────────────────────────────────────────────────────────

@bp.route('/machines')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_MACHINES)
def machines():
    page, per_page = paginate_args(request.args)
    repo = MachineRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['machine_code', 'description'])
    return render_template('master_data/machines.html', **result)


@bp.route('/machines/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def machine_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = MachineRepository(g.db)
        machine = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'Machine', entity_id=machine.id, after_value=data, module='master_data')
        flash_success('Machine created')
        return redirect(url_for('master_data.machines'))
    return render_template('master_data/machine_form.html', data={}, errors={}, machine=None)


@bp.route('/machines/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def machine_edit(id):
    repo = MachineRepository(g.db)
    machine = repo.get_by_id(id)
    if not machine:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Machine', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'Machine', entity_id=id, after_value=data, module='master_data')
        flash_success('Machine updated')
        return redirect(url_for('master_data.machines'))
    data = {c.name: getattr(machine, c.name) for c in machine.__table__.columns}
    return render_template('master_data/machine_form.html', data=data, machine=machine, errors={})


@bp.route('/machines/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def machine_delete(id):
    repo = MachineRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'Machine', entity_id=id, module='master_data')
    flash_success('Machine deleted')
    return redirect(url_for('master_data.machines'))


# ── SKUs ─────────────────────────────────────────────────────────────────

@bp.route('/skus')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_SKUS)
def skus():
    page, per_page = paginate_args(request.args)
    repo = SKURepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['sku_code', 'description'])
    return render_template('master_data/skus.html', **result)


@bp.route('/skus/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def sku_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = SKURepository(g.db)
        sku = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'SKU', entity_id=sku.id, after_value=data, module='master_data')
        flash_success('SKU created')
        return redirect(url_for('master_data.skus'))
    return render_template('master_data/sku_form.html', data={}, errors={}, sku=None)


@bp.route('/skus/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def sku_edit(id):
    repo = SKURepository(g.db)
    sku = repo.get_by_id(id)
    if not sku:
        from app.utils.errors import NotFoundError
        raise NotFoundError('SKU', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))

        # Sync nicotine → CalibrationConstant.n_tgt
        if 'nicotine' in data and sku.sku_code:
            try:
                nic_val = float(data['nicotine']) if data['nicotine'] else None
            except (ValueError, TypeError):
                nic_val = None
            if nic_val is not None:
                from app.services.nicotine_sync import sync_nicotine
                sync_nicotine(fg_code=sku.sku_code, n_tgt_val=nic_val)

        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'SKU', entity_id=id, after_value=data, module='master_data')
        flash_success('SKU updated')
        return redirect(url_for('master_data.skus'))
    data = {c.name: getattr(sku, c.name) for c in sku.__table__.columns}
    return render_template('master_data/sku_form.html', data=data, sku=sku, errors={})


@bp.route('/skus/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def sku_delete(id):
    repo = SKURepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'SKU', entity_id=id, module='master_data')
    flash_success('SKU deleted')
    return redirect(url_for('master_data.skus'))


# ── Tobacco Blend Analysis ───────────────────────────────────────────────

@bp.route('/tobacco-blend-analysis')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_TOBACCO_ANALYSIS)
def tobacco_blend_analysis():
    page, per_page = paginate_args(request.args)
    repo = TobaccoBlendAnalysisRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['blend_name'])
    return render_template('master_data/tobacco_blend_analysis.html', **result)


# ── Formula Constants ────────────────────────────────────────────────────

@bp.route('/formula-constants')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_FORMULA_CONSTANTS)
def formula_constants():
    page, per_page = paginate_args(request.args)
    repo = FormulaConstantRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['name', 'description'])
    return render_template('master_data/formula_constants.html', **result)


@bp.route('/formula-constants/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def formula_constant_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = FormulaConstantRepository(g.db)
        fc = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'FormulaConstant', entity_id=fc.id, after_value=data, module='master_data')
        flash_success('Formula constant created')
        return redirect(url_for('master_data.formula_constants'))
    return render_template('master_data/formula_constant_form.html', data={}, errors={}, constant=None)


@bp.route('/formula-constants/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def formula_constant_edit(id):
    repo = FormulaConstantRepository(g.db)
    fc = repo.get_by_id(id)
    if not fc:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Formula Constant', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'FormulaConstant', entity_id=id, after_value=data, module='master_data')
        flash_success('Formula constant updated')
        return redirect(url_for('master_data.formula_constants'))
    data = {c.name: getattr(fc, c.name) for c in fc.__table__.columns}
    return render_template('master_data/formula_constant_form.html', data=data, constant=fc, errors={})


@bp.route('/formula-constants/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def formula_constant_delete(id):
    repo = FormulaConstantRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'FormulaConstant', entity_id=id, module='master_data')
    flash_success('Formula constant deleted')
    return redirect(url_for('master_data.formula_constants'))


# ── Gamma Constants ──────────────────────────────────────────────────────

@bp.route('/gamma-constants')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_GAMMA_CONSTANTS)
def gamma_constants():
    page, per_page = paginate_args(request.args)
    repo = GammaConstantRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['format', 'selection_criteria'])
    return render_template('master_data/gamma_constants.html', **result)


@bp.route('/gamma-constants/create', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def gamma_constant_create():
    if request.method == 'POST':
        data = request.form.to_dict()
        repo = GammaConstantRepository(g.db)
        gc = repo.create(data)
        g.db.commit()
        AuditLogger.log(AuditAction.CREATE, 'GammaConstant', entity_id=gc.id, after_value=data, module='master_data')
        flash_success('Gamma constant created')
        return redirect(url_for('master_data.gamma_constants'))
    return render_template('master_data/gamma_constant_form.html', data={}, errors={}, constant=None)


@bp.route('/gamma-constants/<id>/edit', methods=['GET', 'POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def gamma_constant_edit(id):
    repo = GammaConstantRepository(g.db)
    gc = repo.get_by_id(id)
    if not gc:
        from app.utils.errors import NotFoundError
        raise NotFoundError('Gamma Constant', id)
    if request.method == 'POST':
        data = request.form.to_dict()
        repo.update(id, data, row_version=int(request.form.get('row_version', 0)))
        g.db.commit()
        AuditLogger.log(AuditAction.UPDATE, 'GammaConstant', entity_id=id, after_value=data, module='master_data')
        flash_success('Gamma constant updated')
        return redirect(url_for('master_data.gamma_constants'))
    data = {c.name: getattr(gc, c.name) for c in gc.__table__.columns}
    return render_template('master_data/gamma_constant_form.html', data=data, constant=gc, errors={})


# ── Reseed Gamma Constants ────────────────────────────────────────────────

@bp.route('/gamma-constants/reseed', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def gamma_constants_reseed():
    """Reseed gamma_constants AND formula_constants with production data."""
    from app.database import get_engine
    from app.services.seed_service import (
        ensure_seed_tables, seed_formula_constants, seed_gamma_constants,
    )

    ensure_seed_tables(get_engine())
    fc_added = seed_formula_constants(g.db)
    added, updated, deactivated = seed_gamma_constants(g.db)
    g.db.commit()

    flash_success(f'Reseeded: Formula constants: {fc_added} added. '
                  f'Gamma: {added} added, {updated} updated, {deactivated} deactivated')
    return redirect(url_for('master_data.gamma_constants'))


@bp.route('/gamma-constants/<id>/delete', methods=['POST'])
@require_auth
@require_permission(Permissions.MASTER_DATA_EDIT)
def gamma_constant_delete(id):
    repo = GammaConstantRepository(g.db)
    repo.soft_delete(id)
    g.db.commit()
    AuditLogger.log(AuditAction.DELETE, 'GammaConstant', entity_id=id, module='master_data')
    flash_success('Gamma constant deleted')
    return redirect(url_for('master_data.gamma_constants'))


# ── Size / CU ────────────────────────────────────────────────────────────

@bp.route('/size-cu')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_SIZE_CU)
def size_cu():
    page, per_page = paginate_args(request.args)
    repo = LookupRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                filters={'category': 'size_cu'},
                                search=request.args.get('q', ''),
                                search_fields=['code', 'display_name'])
    return render_template('master_data/size_cu.html', **result)


# ── KP Tolerance ─────────────────────────────────────────────────────────

@bp.route('/kp-tolerance')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_KP_TOLERANCE)
def kp_tolerance():
    page, per_page = paginate_args(request.args)
    repo = LookupRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                filters={'category': 'kp_tolerance'},
                                search=request.args.get('q', ''),
                                search_fields=['code', 'display_name'])
    return render_template('master_data/kp_tolerance.html', **result)


# ── Plug Length / Cuts ───────────────────────────────────────────────────

@bp.route('/plug-length-cuts')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_PLUG_LENGTH)
def plug_length_cuts():
    page, per_page = paginate_args(request.args)
    repo = LookupRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                filters={'category': 'plug_length_cuts'},
                                search=request.args.get('q', ''),
                                search_fields=['code', 'display_name'])
    return render_template('master_data/plug_length_cuts.html', **result)


# ── App Fields ───────────────────────────────────────────────────────────

@bp.route('/app-fields')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_APP_FIELDS)
def app_fields():
    page, per_page = paginate_args(request.args)
    repo = LookupRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                filters={'category': 'app_fields'},
                                order_by='sort_order',
                                search=request.args.get('q', ''),
                                search_fields=['code', 'display_name'])
    return render_template('master_data/app_fields.html', **result)


# ── Targets & Limits ─────────────────────────────────────────────────────

@bp.route('/targets-limits')
@require_auth
@require_any_permissions(Permissions.MASTER_DATA_VIEW, Permissions.MASTER_DATA_TARGETS_LIMITS)
def targets_limits():
    page, per_page = paginate_args(request.args)
    repo = FGCodeRepository(g.db)
    result = repo.get_paginated(page=page, per_page=per_page,
                                search=request.args.get('q', ''),
                                search_fields=['fg_code', 'brand', 'blend', 'family_name'])
    return render_template('master_data/targets_limits.html', **result)
