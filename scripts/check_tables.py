"""Check what tables exist in MSSQL database."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from app import create_app
from app.database import get_engine, Base
from sqlalchemy import text

# Import all models so Base.metadata knows about them
from app.models.fg_code import FGCode
from app.models.blend_master import BlendMaster
from app.models.calibration_constant import CalibrationConstant
from app.models.physical_parameter import PhysicalParameter
from app.models.lookup import Lookup
from app.models.process_order import ProcessOrder
from app.models.key_variable import ProcessOrderKeyVariable

app = create_app()
with app.app_context():
    engine = get_engine()
    engine.echo = False
    with engine.connect() as conn:
        result = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"))
        tables = [row[0] for row in result]
        print("Tables in database:")
        for t in sorted(tables):
            print(f"  - {t}")

        if 'fg_codes' not in tables:
            print("\n*** fg_codes table does NOT exist - Creating tables now ***")
            Base.metadata.create_all(engine)
            print("Tables created!")
            # Re-check
            result2 = conn.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"))
            tables2 = [row[0] for row in result2]
            print("Tables after creation:")
            for t in sorted(tables2):
                print(f"  - {t}")
        else:
            r = conn.execute(text("SELECT COUNT(*) FROM fg_codes"))
            print(f"\nfg_codes count: {r.scalar()}")
