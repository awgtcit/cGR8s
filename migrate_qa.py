"""Migration script to add new QA columns to qa_analysis table."""
import os
import pyodbc

server = os.environ.get('DB_SERVER', '172.50.35.75,1433')
database = os.environ.get('DB_NAME', 'cGR8s')
uid = os.environ.get('DB_USER', 'sa')
pwd = os.environ.get('DB_PASSWORD')
if not pwd:
    raise SystemExit('DB_PASSWORD environment variable is required')

conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={server};DATABASE={database};UID={uid};PWD={pwd}'
)
cursor = conn.cursor()

# Check existing columns
cursor.execute(
    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
    "WHERE TABLE_NAME='qa_analysis'"
)
existing = {row[0] for row in cursor.fetchall()}
print('Existing columns:', sorted(existing))

# New columns to add
new_cols = {
    'qr_date': 'DATE NULL',
    'npl_date': 'DATE NULL',
    'pack_ov': 'FLOAT NULL',
    'lamina_cpi': 'FLOAT NULL',
    'filling_power': 'FLOAT NULL',
    'filling_power_corr': 'FLOAT NULL',
    'maker_moisture': 'FLOAT NULL',
    'ssi': 'FLOAT NULL',
    'pan_pct': 'FLOAT NULL',
    'total_cig_length': 'FLOAT NULL',
    'circumference_mean': 'FLOAT NULL',
    'circumference_sd': 'FLOAT NULL',
    'cig_dia': 'FLOAT NULL',
    'tip_vf': 'FLOAT NULL',
    'tip_vf_sd': 'FLOAT NULL',
    'filter_pd_mean': 'FLOAT NULL',
    'w_ntm': 'FLOAT NULL',
    'plug_wrap_cu': 'FLOAT NULL',
    'tow': 'NVARCHAR(100) NULL',
    'cig_pdo': 'FLOAT NULL',
    'cig_hardness': 'FLOAT NULL',
    'cig_corr_hardness': 'FLOAT NULL',
    'loose_shorts': 'FLOAT NULL',
    'plug_length': 'FLOAT NULL',
    'mc': 'FLOAT NULL',
    'company': 'NVARCHAR(100) NULL',
}

added = 0
for col_name, col_type in new_cols.items():
    if col_name not in existing:
        sql = f'ALTER TABLE qa_analysis ADD {col_name} {col_type}'
        print(f'Adding: {col_name}')
        cursor.execute(sql)
        added += 1
    else:
        print(f'Exists: {col_name}')

conn.commit()
conn.close()
print(f'\nMigration complete! Added {added} new columns.')
