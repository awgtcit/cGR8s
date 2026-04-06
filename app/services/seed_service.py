"""
Shared seeding logic for formula_constants and gamma_constants.
Used by both the admin reseed route and the CLI fix_tables script.
"""
from app.models.formula_constant import FormulaConstant
from app.models.gamma_constant import GammaConstant
from app.models.base import generate_uuid
from app.services.gamma_seed_data import GAMMA_SEED_DATA, GAMMA_KNOWN_FORMATS

FORMULA_SEED_DATA = [
    ('Alpha', 10.0, 'Dilution model coefficient α'),
    ('Beta', -0.043, 'Dilution model exponent β (negative)'),
    ('Delta', -0.056, 'Filtration model exponent δ (negative)'),
    ('Dust_Moisture', 9.0, 'Default dust moisture %'),
    ('Max_VF', 65.0, 'Maximum ventilation factor'),
    ('Min_PD', 220.0, 'Minimum pressure drop'),
    ('Max_PD', 450.0, 'Maximum pressure drop'),
    ('NCG', 10000.0, 'Nominal cigarette group size'),
]


def ensure_seed_tables(engine):
    """Create formula_constants and gamma_constants tables if missing."""
    if not engine:
        return
    for model in (FormulaConstant, GammaConstant):
        try:
            model.__table__.create(engine, checkfirst=True)
        except Exception:
            pass


def seed_formula_constants(session):
    """Insert missing formula constants. Returns count added."""
    added = 0
    for name, value, desc in FORMULA_SEED_DATA:
        existing = session.query(FormulaConstant).filter(
            FormulaConstant.name == name
        ).first()
        if not existing:
            session.add(FormulaConstant(
                id=generate_uuid(), name=name, value=value,
                description=desc, is_active=True,
            ))
            added += 1
    return added


def seed_gamma_constants(session):
    """Upsert gamma constants and deactivate old entries.
    Returns (added, updated, deactivated) counts.
    """
    added, updated, deactivated = 0, 0, 0

    for fmt, pl, cond, sel, val in GAMMA_SEED_DATA:
        existing = session.query(GammaConstant).filter(
            GammaConstant.format == fmt,
            GammaConstant.plug_length == pl,
            GammaConstant.condition == cond,
        ).first()
        if not existing:
            session.add(GammaConstant(
                id=generate_uuid(), format=fmt, plug_length=pl,
                condition=cond, selection_criteria=sel, value=val,
                is_active=True,
            ))
            added += 1
        elif existing.value != val or not existing.is_active:
            existing.value = val
            existing.selection_criteria = sel
            existing.is_active = True
            updated += 1

    old = session.query(GammaConstant).filter(
        ~GammaConstant.format.in_(GAMMA_KNOWN_FORMATS),
        GammaConstant.is_active == True,  # noqa: E712
    ).all()
    for o in old:
        o.is_active = False
        deactivated += 1

    return added, updated, deactivated
