"""
Seed script for FormulaConstant and GammaConstant tables.
Run once after table creation: python scripts/seed_formula_constants.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_engine, get_session, init_db
from app.models.formula_constant import FormulaConstant
from app.models.gamma_constant import GammaConstant
from app.models.base import generate_uuid
from app.services.gamma_seed_data import GAMMA_SEED_DATA, GAMMA_KNOWN_FORMATS


def seed():
    """Create FormulaConstant & GammaConstant tables and insert seed data."""
    # Need to initialize the app to get db config
    from app import create_app
    app = create_app()

    with app.app_context():
        engine = get_engine()

        # Create only the new tables (safe – won't drop existing ones)
        FormulaConstant.__table__.create(engine, checkfirst=True)
        GammaConstant.__table__.create(engine, checkfirst=True)

        session = get_session()

        try:
            # ─── Formula Constants ────────────────────────────────────
            constants = [
                ('Alpha', 10.0, 'Dilution model coefficient α'),
                ('Beta', -0.043, 'Dilution model exponent β (negative)'),
                ('Delta', -0.056, 'Filtration model exponent δ (negative)'),
                ('Dust_Moisture', 9.0, 'Default dust moisture %'),
                ('Max_VF', 65.0, 'Maximum ventilation factor'),
                ('Min_PD', 220.0, 'Minimum pressure drop'),
                ('Max_PD', 450.0, 'Maximum pressure drop'),
                ('NCG', 10000.0, 'Nominal cigarette group size'),
            ]

            for name, value, desc in constants:
                existing = session.query(FormulaConstant).filter(
                    FormulaConstant.name == name
                ).first()
                if not existing:
                    fc = FormulaConstant(
                        id=generate_uuid(),
                        name=name,
                        value=value,
                        description=desc,
                        is_active=True,
                    )
                    session.add(fc)
                    print(f'  + FormulaConstant: {name} = {value}')
                else:
                    print(f'  ~ FormulaConstant: {name} already exists (value={existing.value})')

            # ─── Gamma Constants (lookup table) ───────────────────────
            # Data from shared module – full format strings from production Excel.
            for fmt, pl, cond, sel, val in GAMMA_SEED_DATA:
                existing = session.query(GammaConstant).filter(
                    GammaConstant.format == fmt,
                    GammaConstant.plug_length == pl,
                    GammaConstant.condition == cond,
                ).first()
                if not existing:
                    gc = GammaConstant(
                        id=generate_uuid(),
                        format=fmt,
                        plug_length=pl,
                        condition=cond,
                        selection_criteria=sel,
                        value=val,
                        is_active=True,
                    )
                    session.add(gc)
                    print(f'  + GammaConstant: {fmt}/{pl}/{cond} = {val}')
                else:
                    if existing.value != val or existing.selection_criteria != sel:
                        existing.value = val
                        existing.selection_criteria = sel
                        existing.is_active = True
                        print(f'  * GammaConstant: {fmt}/{pl}/{cond} updated → {val}')
                    else:
                        print(f'  ~ GammaConstant: {fmt}/{pl}/{cond} already correct (value={existing.value})')

            # Deactivate old short-prefix entries that no longer match
            old_prefixes = session.query(GammaConstant).filter(
                ~GammaConstant.format.in_(GAMMA_KNOWN_FORMATS),
                GammaConstant.is_active == True,  # noqa: E712
            ).all()
            for old in old_prefixes:
                old.is_active = False
                print(f'  - Deactivated old entry: {old.format}/{old.plug_length}/{old.condition}')


            session.commit()
            print('\nSeed complete.')

        except Exception as e:
            session.rollback()
            print(f'\nError: {e}')
            raise
        finally:
            session.close()


if __name__ == '__main__':
    seed()
