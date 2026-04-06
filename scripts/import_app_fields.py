"""Import AppFields data into lookups table with category='app_fields'."""
import uuid
from sqlalchemy import create_engine, text

ENGINE_URL = (
    "mssql+pyodbc://sa:Admin%40123@172.50.35.75:1433/cGR8s"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
)
engine = create_engine(ENGINE_URL)

# AppFields from Excel Data sheet (columns AK-AL)
APP_FIELDS = [
    (1, "FG Code"),
    (2, "Cig Code"),
    (3, "Blend Code"),
    (4, "Blend"),
    (5, "Filter Code"),
    (6, "Brand"),
    (7, "Format"),
    (8, "FG GTIN"),
    (9, "Blend GTIN"),
    (10, "Circumference Mean"),
    (11, "Cig Dia"),
    (12, "Cig Length"),
    (13, "NTM Wt. Mean"),
    (14, "Filter Weight"),
    (15, "Plug Length"),
    (16, "Tip Ventilation (Vf)"),
    (17, "Filter PD"),
    (18, "Maker Moisture"),
    (19, "Filter Rod Length"),
    (20, "Rod Length"),
]


def main():
    with engine.begin() as conn:
        imported = 0
        for sn, field_name in APP_FIELDS:
            exists = conn.execute(
                text("SELECT 1 FROM lookups WHERE category = 'app_fields' AND code = :code"),
                {'code': str(sn)}
            ).fetchone()
            if exists:
                print(f"  Skipped SN {sn} ({field_name}) - already exists")
                continue
            conn.execute(
                text("""INSERT INTO lookups (id, category, code, display_name, sort_order, is_active, created_at, updated_at)
                         VALUES (:id, 'app_fields', :code, :dn, :so, 1, GETDATE(), GETDATE())"""),
                {'id': str(uuid.uuid4()), 'code': str(sn), 'dn': field_name, 'so': sn}
            )
            imported += 1
            print(f"  Imported SN {sn}: {field_name}")

        print(f"\nTotal imported: {imported} app fields")


if __name__ == '__main__':
    main()
