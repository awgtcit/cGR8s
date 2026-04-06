"""Quick check of linked data in DB."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('FLASK_ENV', 'development')
from dotenv import load_dotenv
load_dotenv(override=True)

from app import create_app
from app.database import get_session
from sqlalchemy import text

app = create_app('development')
with app.app_context():
    s = get_session()

    # Check calibration_constants
    cals = s.execute(text(
        "SELECT TOP 5 c.fg_code_id, c.alpha, c.beta, c.gamma, c.delta, c.n_tgt, f.fg_code "
        "FROM calibration_constants c JOIN fg_codes f ON c.fg_code_id = f.id "
        "WHERE c.alpha != 0 OR c.beta != 0 OR c.n_tgt != 0"
    )).fetchall()
    print(f"\nCalibration with non-zero data ({len(cals)} shown):")
    for r in cals:
        print(f"  {r.fg_code}: alpha={r.alpha}, beta={r.beta}, gamma={r.gamma}, delta={r.delta}, n_tgt={r.n_tgt}")

    # Count
    total_cal = s.execute(text("SELECT COUNT(*) FROM calibration_constants")).scalar()
    nonzero_cal = s.execute(text("SELECT COUNT(*) FROM calibration_constants WHERE alpha != 0 OR beta != 0")).scalar()
    print(f"\nTotal calibrations: {total_cal}, Non-zero: {nonzero_cal}")

    # Check physical_parameters
    phys = s.execute(text(
        "SELECT TOP 5 p.fg_code_id, p.p_cu, p.t_vnt, p.f_pd, p.m_ip, f.fg_code "
        "FROM physical_parameters p JOIN fg_codes f ON p.fg_code_id = f.id "
        "WHERE p.p_cu != 0 OR p.t_vnt != 0 OR p.f_pd != 0"
    )).fetchall()
    print(f"\nPhysical params with non-zero data ({len(phys)} shown):")
    for r in phys:
        print(f"  {r.fg_code}: p_cu={r.p_cu}, t_vnt={r.t_vnt}, f_pd={r.f_pd}, m_ip={r.m_ip}")

    total_phys = s.execute(text("SELECT COUNT(*) FROM physical_parameters")).scalar()
    nonzero_phys = s.execute(text("SELECT COUNT(*) FROM physical_parameters WHERE p_cu != 0 OR t_vnt != 0 OR f_pd != 0")).scalar()
    print(f"\nTotal physical params: {total_phys}, Non-zero: {nonzero_phys}")

    # Check blend_masters
    blends = s.execute(text("SELECT TOP 5 blend_code, blend_name, n_bld FROM blend_masters WHERE n_bld != 0")).fetchall()
    print(f"\nBlend masters with n_bld != 0 ({len(blends)} shown):")
    for r in blends:
        print(f"  {r.blend_code}: {r.blend_name}, n_bld={r.n_bld}")

    s.close()
