# cGR8s – Comprehensive Goods Reconciliation at Secondary

Production-grade Flask 3 enterprise application for tobacco manufacturing goods reconciliation, replacing the legacy Excel/VBA system.

## Features

- **FG Code Management** – Create and manage Finished Goods codes with maker-checker workflow
- **Target Weight Calculator** – Calculate target weights from 5 key variables (N_BLD, P_CU, T_VNT, F_PD, M_IP)
- **NPL Calculation** – Non-Process Loss percentage with TAC/TTC analysis
- **Product Run Optimizer** – Three optimization methods (adjustment, manual, direct) with tolerance validation
- **Process Orders** – Full lifecycle management with status transitions
- **QA Workflow** – Quality analysis entry, approval/rejection with audit trail
- **Batch Processing** – Thread-based background job queue for bulk operations
- **Reports** – PDF (WeasyPrint) and Excel (openpyxl) generation with branded styling
- **Audit Trail** – Full audit logging of all user actions
- **External Authentication** – JWT validation via Auth-App integration

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask 3.0, Python 3.11+ |
| ORM | SQLAlchemy 2.0 |
| Database | Microsoft SQL Server (pyodbc) |
| Migrations | Alembic |
| Auth | External Auth-App (JWT) |
| PDF | WeasyPrint |
| Excel | openpyxl |
| Frontend | Bootstrap 5.3, HTMX 1.9, Alpine.js 3.14 |
| Background Jobs | Threading + DB queue |

## Quick Start

### 1. Clone & Setup Environment

```powershell
cd cGR8s
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
Copy-Item .env.example .env
# Edit .env with your database and auth settings
```

Key settings in `.env`:

```ini
SECRET_KEY=your-secret-key
DB_SERVER=your-sql-server
DB_NAME=cGR8s
DB_AUTH_MODE=windows          # or 'sql'
DB_USER=sa                    # if sql auth
DB_PASSWORD=yourpassword      # if sql auth
AUTH_APP_URL=http://ams-it-126:5000
AUTH_API_KEY=your-api-key
```

### 3. Initialize Database

```powershell
alembic upgrade head
```

### 4. Run Application

```powershell
python run.py
```

The application starts on **http://localhost:5050**

## Project Structure

```
cGR8s/
├── run.py                          # Entry point
├── requirements.txt                # Dependencies
├── .env.example                    # Environment template
├── alembic.ini                     # Migration config
├── app/
│   ├── __init__.py                 # App factory
│   ├── database.py                 # DB engine & session
│   ├── config/
│   │   ├── settings.py             # Flask config classes
│   │   └── constants.py            # Enums & constants
│   ├── models/                     # SQLAlchemy models (24 classes)
│   ├── repositories/               # Data access layer (20+ repos)
│   ├── services/                   # Business logic
│   │   ├── target_weight_calc.py   # Target weight calculator
│   │   ├── npl_calc.py             # NPL calculator
│   │   ├── optimizer.py            # Product run optimizer
│   │   ├── batch_processor.py      # Background job processor
│   │   └── report_generator.py     # PDF & Excel reports
│   ├── modules/                    # Blueprint route handlers
│   │   ├── dashboard/
│   │   ├── admin/
│   │   ├── fg_codes/
│   │   ├── master_data/
│   │   ├── target_weight/
│   │   ├── process_orders/
│   │   ├── npl/
│   │   ├── qa/
│   │   ├── optimizer/
│   │   ├── batch/
│   │   └── reports/
│   ├── auth/                       # Auth-App integration
│   ├── audit/                      # Audit logging
│   ├── rules/                      # Validation engine
│   ├── utils/                      # Helpers & error handling
│   └── reports/templates/          # PDF report templates
├── templates/                      # Jinja2 HTML templates
├── static/                         # CSS, JS assets
├── migrations/                     # Alembic migrations
└── tests/                          # pytest test suite
```

## Authentication

cGR8s uses an external Auth-App for authentication. Users authenticate via the Auth-App and receive JWT tokens. The `AUTH_APP_URL` in `.env` (or `system_config` table) points to the Auth-App instance.

Required headers: `Authorization: Bearer <token>`

## Database

Supports both **Windows Authentication** and **SQL Server Authentication**:

- `DB_AUTH_MODE=windows` – Uses `Trusted_Connection=yes`
- `DB_AUTH_MODE=sql` – Uses `DB_USER` and `DB_PASSWORD`

ODBC Driver 17 for SQL Server is required.

## Running Tests

```powershell
pytest tests/ -v
```

## Brand Colors (AL WAHDANIA)

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Green | #0D6B3C | Headers, buttons, accents |
| Secondary Green | #43B649 | Success states, highlights |
| Forest | #084C2E | Deep accents |
| Mint | #DDF3E4 | Backgrounds, badges |
| Background | #F5F7F6 | Page background |
| Text | #183026 | Body text |

## License

Internal use only – AL WAHDANIA Group Trading Company.
