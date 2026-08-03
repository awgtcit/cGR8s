"""Seed formula + gamma constants via the app's SeedService (idempotent upsert).

Uses the complete gamma table in app/services/gamma_seed_data.py. Safe to re-run.
  .venv/Scripts/python.exe scripts/seed_constants.py
"""
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            override=True)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.seed_service import seed_formula_constants, seed_gamma_constants


def main():
    drv = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    eng = create_engine(
        f"mssql+pyodbc://{urllib.parse.quote_plus(os.getenv('DB_USER'))}:"
        f"{urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_SERVER')},"
        f"{os.getenv('DB_PORT', '1433')}/{os.getenv('DB_NAME')}"
        f"?driver={urllib.parse.quote_plus(drv)}", connect_args={"timeout": 30})
    session = sessionmaker(bind=eng)()
    try:
        fa = seed_formula_constants(session)
        ga, gu, gd = seed_gamma_constants(session)
        session.commit()
        print(f"formula: +{fa}   gamma: +{ga} updated {gu} deactivated {gd}")
        rows = session.execute(text(
            "SELECT format, plug_length, condition, value, is_active FROM gamma_constants "
            "WHERE format='SL20SE' ORDER BY plug_length, condition")).fetchall()
        print("SL20SE rows:", [tuple(r) for r in rows])
        print("active gamma count:", session.execute(text(
            "SELECT COUNT(*) FROM gamma_constants WHERE is_active=1")).scalar())
    finally:
        session.close()


if __name__ == "__main__":
    main()
