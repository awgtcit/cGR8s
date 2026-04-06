"""Check current DB state vs Excel data."""
from sqlalchemy import create_engine, text

engine = create_engine('mssql+pyodbc://sa:Admin%40123@172.50.35.75/cGR8s?driver=ODBC+Driver+17+for+SQL+Server')

with engine.connect() as c:
    # Current DB counts
    for t in ['fg_codes', 'blend_master', 'calibration_constants', 'physical_parameters', 'lookups']:
        try:
            r = c.execute(text(f"SELECT COUNT(*) FROM {t} WHERE is_deleted=0")).scalar()
        except Exception:
            r = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"{t}: {r} rows")

    # Check all tables
    tables = c.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")).fetchall()
    print(f"\nAll tables: {[t[0] for t in tables]}")

    # Check FG Code columns in DB
    cols = c.execute(text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='fg_codes' ORDER BY ORDINAL_POSITION")).fetchall()
    print(f"\nfg_codes columns ({len(cols)}): {[col[0] for col in cols]}")

    # Sample FG codes - check what blend_codes exist
    blend_codes = c.execute(text("SELECT DISTINCT blend_code FROM blend_master WHERE is_deleted=0 ORDER BY blend_code")).fetchall()
    print(f"\nBlend codes in DB ({len(blend_codes)}): {[b[0] for b in blend_codes]}")

    # Check lookups categories
    cats = c.execute(text("SELECT category, COUNT(*) FROM lookups GROUP BY category ORDER BY category")).fetchall()
    print(f"\nLookup categories: {[(cat[0], cat[1]) for cat in cats]}")
