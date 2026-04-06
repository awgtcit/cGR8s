"""Quick script to check and fix formula_constants + gamma_constants tables."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress verbose SQL logging
import logging
logging.disable(logging.INFO)

from dotenv import load_dotenv
load_dotenv(override=True)
os.environ['DEBUG'] = '0'

from app import create_app
from app.database import get_engine, get_session
from app.services.seed_service import (
    ensure_seed_tables, seed_formula_constants, seed_gamma_constants,
)

app = create_app()
with app.app_context():
    engine = get_engine()
    ensure_seed_tables(engine)
    print('Tables ensured.')

    session = get_session()
    try:
        fc_added = seed_formula_constants(session)
        print(f'Formula constants: {fc_added} added.')

        added, updated, deactivated = seed_gamma_constants(session)
        print(f'Gamma: {added} added, {updated} updated, {deactivated} deactivated.')

        session.commit()

        # Verify gamma lookup
        from app.models.gamma_constant import GammaConstant
        test = session.query(GammaConstant).filter(
            GammaConstant.format == 'KS20SE',
            GammaConstant.plug_length == 21,
            GammaConstant.condition == True,  # noqa: E712
        ).first()
        print(f'KS20SE/21/TRUE gamma = {test.value if test else "NOT FOUND"}')
    finally:
        session.close()
