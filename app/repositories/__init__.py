"""
Concrete repository implementations for all domain entities.
"""
from app.repositories.base_repository import BaseRepository
from app.models.fg_code import FGCode
from app.models.blend_master import BlendMaster
from app.models.physical_parameter import PhysicalParameter
from app.models.calibration_constant import CalibrationConstant
from app.models.product_version import ProductVersion
from app.models.process_order import ProcessOrder
from app.models.key_variable import ProcessOrderKeyVariable
from app.models.target_weight_result import TargetWeightResult
from app.models.npl import NPLInput, NPLResult
from app.models.qa import QAAnalysis, QAUpdate
from app.models.optimizer import OptimizerRun, OptimizerInput, OptimizerResult, OptimizerLimit
from app.models.report import Report, FormulaDefinition
from app.models.batch import BatchJob, BatchJobItem
from app.models.audit_log import AuditLog, MasterDataChangeLog
from app.models.system_config import SystemConfig
from app.models.lookup import Lookup
from app.models.machine import Machine
from app.models.sku import SKU
from app.models.tobacco_blend_analysis import TobaccoBlendAnalysis
from app.models.formula_constant import FormulaConstant
from app.models.gamma_constant import GammaConstant


class FGCodeRepository(BaseRepository[FGCode]):
    def __init__(self, session=None):
        super().__init__(FGCode, session)

    def get_by_fg_code(self, fg_code: str):
        return self.session.query(FGCode).filter(
            FGCode.fg_code == fg_code,
            FGCode.is_deleted == False  # noqa: E712
        ).first()

    def get_by_code(self, fg_code: str):
        """Alias for get_by_fg_code for API consistency."""
        return self.get_by_fg_code(fg_code)

    def get_limited(self, limit: int = 200, search: str = ""):
        """Get limited number of FG codes with optional search."""
        from sqlalchemy import or_
        q = self.session.query(FGCode).filter(FGCode.is_deleted == False)  # noqa: E712

        if search:
            q = q.filter(or_(
                FGCode.fg_code.ilike(f'%{search}%'),
                FGCode.brand.ilike(f'%{search}%')
            ))

        return q.order_by(FGCode.fg_code).limit(limit).all()

    def count_all(self):
        """Count total number of active FG codes."""
        return self.session.query(FGCode).filter(FGCode.is_deleted == False).count()  # noqa: E712

    def get_fg_code_map(self, ids: list):
        """Return {id: fg_code} dict for a list of FG code IDs in a single query."""
        if not ids:
            return {}
        rows = self.session.query(FGCode.id, FGCode.fg_code).filter(
            FGCode.id.in_(ids)
        ).all()
        return {r.id: r.fg_code for r in rows}

    def get_fg_blend_map(self, ids: list):
        """Return {id: blend} dict for a list of FG code IDs in a single query."""
        if not ids:
            return {}
        rows = self.session.query(FGCode.id, FGCode.blend).filter(
            FGCode.id.in_(ids)
        ).all()
        return {r.id: r.blend for r in rows}

    def create(self, data: dict):
        """Create FG code from dict data."""
        fg_code = FGCode(**data)
        return super().create(fg_code)


class BlendMasterRepository(BaseRepository[BlendMaster]):
    def __init__(self, session=None):
        super().__init__(BlendMaster, session)

    def get_by_blend_code(self, blend_code: str):
        return self.session.query(BlendMaster).filter(
            BlendMaster.blend_code == blend_code,
            BlendMaster.is_deleted == False  # noqa: E712
        ).first()


class PhysicalParameterRepository(BaseRepository[PhysicalParameter]):
    def __init__(self, session=None):
        super().__init__(PhysicalParameter, session)

    def get_by_fg_code_id(self, fg_code_id: str):
        return self.session.query(PhysicalParameter).filter(
            PhysicalParameter.fg_code_id == fg_code_id
        ).first()


class CalibrationConstantRepository(BaseRepository[CalibrationConstant]):
    def __init__(self, session=None):
        super().__init__(CalibrationConstant, session)

    def get_by_fg_code_id(self, fg_code_id: str):
        return self.session.query(CalibrationConstant).filter(
            CalibrationConstant.fg_code_id == fg_code_id
        ).first()


class ProductVersionRepository(BaseRepository[ProductVersion]):
    def __init__(self, session=None):
        super().__init__(ProductVersion, session)

    def get_latest_version(self, fg_code_id: str):
        return self.session.query(ProductVersion).filter(
            ProductVersion.fg_code_id == fg_code_id,
            ProductVersion.is_deleted == False  # noqa: E712
        ).order_by(ProductVersion.version_number.desc()).first()


class ProcessOrderRepository(BaseRepository[ProcessOrder]):
    def __init__(self, session=None):
        super().__init__(ProcessOrder, session)

    def get_by_order_number(self, order_number: str):
        return self.session.query(ProcessOrder).filter(
            ProcessOrder.process_order_number == order_number,
            ProcessOrder.is_deleted == False  # noqa: E712
        ).first()

    def exists_by_order_id(self, order_id: str):
        """Check if process order ID already exists."""
        return self.session.query(ProcessOrder).filter(
            ProcessOrder.process_order_number == order_id,
            ProcessOrder.is_deleted == False  # noqa: E712
        ).first() is not None

    def create(self, data: dict):
        """Create process order from dict data."""
        process_order = ProcessOrder(**data)
        return super().create(process_order)

    def get_by_fg_code(self, fg_code_id: str):
        return self.session.query(ProcessOrder).filter(
            ProcessOrder.fg_code_id == fg_code_id,
            ProcessOrder.is_deleted == False  # noqa: E712
        ).order_by(ProcessOrder.process_date.desc()).all()

    def get_po_number_map(self, ids: list):
        """Return {id: process_order_number} dict for a list of PO IDs in a single query."""
        if not ids:
            return {}
        rows = self.session.query(ProcessOrder.id, ProcessOrder.process_order_number).filter(
            ProcessOrder.id.in_(ids)
        ).all()
        return {r.id: r.process_order_number for r in rows}

    def get_last_run_date(self, fg_code_id: str):
        po = self.session.query(ProcessOrder).filter(
            ProcessOrder.fg_code_id == fg_code_id,
            ProcessOrder.is_deleted == False  # noqa: E712
        ).order_by(ProcessOrder.process_date.desc()).first()
        return po.process_date if po else None

    def get_by_order_numbers(self, order_numbers: list):
        """Bulk fetch POs by order numbers. Returns {number: PO} dict."""
        if not order_numbers:
            return {}
        rows = self.session.query(ProcessOrder).filter(
            ProcessOrder.process_order_number.in_(order_numbers),
            ProcessOrder.is_deleted == False  # noqa: E712
        ).all()
        return {r.process_order_number: r for r in rows}


class KeyVariableRepository(BaseRepository[ProcessOrderKeyVariable]):
    def __init__(self, session=None):
        super().__init__(ProcessOrderKeyVariable, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(ProcessOrderKeyVariable).filter(
            ProcessOrderKeyVariable.process_order_id == process_order_id
        ).first()


class TargetWeightResultRepository(BaseRepository[TargetWeightResult]):
    def __init__(self, session=None):
        super().__init__(TargetWeightResult, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(TargetWeightResult).filter(
            TargetWeightResult.process_order_id == process_order_id
        ).order_by(TargetWeightResult.calculated_at.desc()).first()

    def get_by_process_orders(self, po_ids: list):
        """Bulk fetch most recent TW records. Returns {po_id: TW} dict."""
        if not po_ids:
            return {}
        from sqlalchemy import func
        sub = self.session.query(
            TargetWeightResult.process_order_id,
            func.max(TargetWeightResult.calculated_at).label('max_at')
        ).filter(
            TargetWeightResult.process_order_id.in_(po_ids)
        ).group_by(TargetWeightResult.process_order_id).subquery()
        rows = self.session.query(TargetWeightResult).join(
            sub, (TargetWeightResult.process_order_id == sub.c.process_order_id)
            & (TargetWeightResult.calculated_at == sub.c.max_at)
        ).all()
        return {r.process_order_id: r for r in rows}


class NPLInputRepository(BaseRepository[NPLInput]):
    def __init__(self, session=None):
        super().__init__(NPLInput, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(NPLInput).filter(
            NPLInput.process_order_id == process_order_id
        ).order_by(NPLInput.created_at.desc()).first()

    def get_by_process_orders(self, po_ids: list):
        """Bulk fetch most recent NPL inputs. Returns {po_id: NPLInput} dict."""
        if not po_ids:
            return {}
        from sqlalchemy import func
        sub = self.session.query(
            NPLInput.process_order_id,
            func.max(NPLInput.created_at).label('max_at')
        ).filter(
            NPLInput.process_order_id.in_(po_ids)
        ).group_by(NPLInput.process_order_id).subquery()
        rows = self.session.query(NPLInput).join(
            sub, (NPLInput.process_order_id == sub.c.process_order_id)
            & (NPLInput.created_at == sub.c.max_at)
        ).all()
        return {r.process_order_id: r for r in rows}


class NPLResultRepository(BaseRepository[NPLResult]):
    def __init__(self, session=None):
        super().__init__(NPLResult, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(NPLResult).filter(
            NPLResult.process_order_id == process_order_id
        ).order_by(NPLResult.calculated_at.desc()).first()

    def get_by_process_orders(self, po_ids: list):
        """Bulk fetch most recent NPL records. Returns {po_id: NPL} dict."""
        if not po_ids:
            return {}
        from sqlalchemy import func
        sub = self.session.query(
            NPLResult.process_order_id,
            func.max(NPLResult.calculated_at).label('max_at')
        ).filter(
            NPLResult.process_order_id.in_(po_ids)
        ).group_by(NPLResult.process_order_id).subquery()
        rows = self.session.query(NPLResult).join(
            sub, (NPLResult.process_order_id == sub.c.process_order_id)
            & (NPLResult.calculated_at == sub.c.max_at)
        ).all()
        return {r.process_order_id: r for r in rows}


class QAAnalysisRepository(BaseRepository[QAAnalysis]):
    def __init__(self, session=None):
        super().__init__(QAAnalysis, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(QAAnalysis).filter(
            QAAnalysis.process_order_id == process_order_id
        ).order_by(QAAnalysis.analyzed_at.desc()).first()

    def get_by_process_orders(self, po_ids: list):
        """Bulk fetch most recent QA records for a list of PO IDs. Returns {po_id: QA} dict."""
        if not po_ids:
            return {}
        from sqlalchemy import func
        # Subquery: latest analyzed_at per PO
        sub = self.session.query(
            QAAnalysis.process_order_id,
            func.max(QAAnalysis.analyzed_at).label('max_at')
        ).filter(
            QAAnalysis.process_order_id.in_(po_ids)
        ).group_by(QAAnalysis.process_order_id).subquery()
        rows = self.session.query(QAAnalysis).join(
            sub, (QAAnalysis.process_order_id == sub.c.process_order_id)
            & (QAAnalysis.analyzed_at == sub.c.max_at)
        ).all()
        return {r.process_order_id: r for r in rows}


    def get_latest_by_fg_code_ids(self, fg_code_ids: list, exclude_po_ids: list = None):
        """Get the most recent QA record per fg_code_id (for auto-fill from previous production).

        Returns {fg_code_id: QAAnalysis} dict.
        """
        if not fg_code_ids:
            return {}
        from sqlalchemy import func
        from app.models.process_order import ProcessOrder
        # Subquery: latest analyzed_at per fg_code_id
        sub = self.session.query(
            ProcessOrder.fg_code_id,
            func.max(QAAnalysis.analyzed_at).label('max_at')
        ).join(QAAnalysis, QAAnalysis.process_order_id == ProcessOrder.id
        ).filter(ProcessOrder.fg_code_id.in_(fg_code_ids))
        if exclude_po_ids:
            sub = sub.filter(~QAAnalysis.process_order_id.in_(exclude_po_ids))
        sub = sub.group_by(ProcessOrder.fg_code_id).subquery()
        # Main query: select QA + fg_code_id in one shot (no N+1)
        rows = self.session.query(QAAnalysis, ProcessOrder.fg_code_id).join(
            ProcessOrder, QAAnalysis.process_order_id == ProcessOrder.id
        ).join(
            sub, (ProcessOrder.fg_code_id == sub.c.fg_code_id)
            & (QAAnalysis.analyzed_at == sub.c.max_at)
        ).filter(ProcessOrder.fg_code_id.in_(fg_code_ids))
        if exclude_po_ids:
            rows = rows.filter(~QAAnalysis.process_order_id.in_(exclude_po_ids))
        return {fg_id: qa for qa, fg_id in rows.all()}


class QAUpdateRepository(BaseRepository[QAUpdate]):
    def __init__(self, session=None):
        super().__init__(QAUpdate, session)


class OptimizerRunRepository(BaseRepository[OptimizerRun]):
    def __init__(self, session=None):
        super().__init__(OptimizerRun, session)

    def get_by_process_order(self, process_order_id: str):
        return self.session.query(OptimizerRun).filter(
            OptimizerRun.process_order_id == process_order_id
        ).order_by(OptimizerRun.started_at.desc()).all()


class OptimizerInputRepository(BaseRepository[OptimizerInput]):
    def __init__(self, session=None):
        super().__init__(OptimizerInput, session)


class OptimizerResultRepository(BaseRepository[OptimizerResult]):
    def __init__(self, session=None):
        super().__init__(OptimizerResult, session)

    def get_by_run(self, run_id: str):
        return self.session.query(OptimizerResult).filter(
            OptimizerResult.optimizer_run_id == run_id
        ).first()


class OptimizerLimitRepository(BaseRepository[OptimizerLimit]):
    def __init__(self, session=None):
        super().__init__(OptimizerLimit, session)

    def get_limits_for_fg(self, fg_code_id: str = None):
        """Get limits for a specific FG code, falling back to global defaults."""
        q = self.session.query(OptimizerLimit).filter(
            OptimizerLimit.is_active == True  # noqa: E712
        )
        if fg_code_id:
            from sqlalchemy import or_
            q = q.filter(or_(
                OptimizerLimit.fg_code_id == fg_code_id,
                OptimizerLimit.fg_code_id == None  # noqa: E711
            ))
        else:
            q = q.filter(OptimizerLimit.fg_code_id == None)  # noqa: E711
        return q.all()


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session=None):
        super().__init__(Report, session)


class FormulaDefinitionRepository(BaseRepository[FormulaDefinition]):
    def __init__(self, session=None):
        super().__init__(FormulaDefinition, session)

    def get_by_code(self, formula_code: str):
        return self.session.query(FormulaDefinition).filter(
            FormulaDefinition.formula_code == formula_code
        ).first()


class BatchJobRepository(BaseRepository[BatchJob]):
    def __init__(self, session=None):
        super().__init__(BatchJob, session)


class BatchJobItemRepository(BaseRepository[BatchJobItem]):
    def __init__(self, session=None):
        super().__init__(BatchJobItem, session)

    def get_by_batch_job(self, batch_job_id: str):
        return self.session.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id
        ).order_by(BatchJobItem.sequence).all()


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session=None):
        super().__init__(AuditLog, session)


class MasterDataChangeLogRepository(BaseRepository[MasterDataChangeLog]):
    def __init__(self, session=None):
        super().__init__(MasterDataChangeLog, session)


class SystemConfigRepository(BaseRepository[SystemConfig]):
    def __init__(self, session=None):
        super().__init__(SystemConfig, session)

    def get_by_key(self, key: str):
        return self.session.query(SystemConfig).filter(
            SystemConfig.config_key == key
        ).first()

    def get_value(self, key: str, default=None):
        cfg = self.get_by_key(key)
        return cfg.config_value if cfg else default


class LookupRepository(BaseRepository[Lookup]):
    def __init__(self, session=None):
        super().__init__(Lookup, session)

    def get_by_category(self, category: str):
        return self.session.query(Lookup).filter(
            Lookup.category == category,
            Lookup.is_active == True  # noqa: E712
        ).order_by(Lookup.sort_order).all()


class MachineRepository(BaseRepository[Machine]):
    def __init__(self, session=None):
        super().__init__(Machine, session)

    def get_by_machine_code(self, machine_code: str):
        return self.session.query(Machine).filter(
            Machine.machine_code == machine_code
        ).first()


class SKURepository(BaseRepository[SKU]):
    def __init__(self, session=None):
        super().__init__(SKU, session)

    def get_by_sku_code(self, sku_code: str):
        return self.session.query(SKU).filter(
            SKU.sku_code == sku_code
        ).first()


class TobaccoBlendAnalysisRepository(BaseRepository[TobaccoBlendAnalysis]):
    def __init__(self, session=None):
        super().__init__(TobaccoBlendAnalysis, session)

    def get_by_blend_name(self, blend_name: str):
        return self.session.query(TobaccoBlendAnalysis).filter(
            TobaccoBlendAnalysis.blend_name == blend_name
        ).order_by(
            TobaccoBlendAnalysis.period_year,
            TobaccoBlendAnalysis.period_month
        ).all()


class FormulaConstantRepository(BaseRepository[FormulaConstant]):
    def __init__(self, session=None):
        super().__init__(FormulaConstant, session)

    def get_by_name(self, name: str):
        return self.session.query(FormulaConstant).filter(
            FormulaConstant.name == name,
            FormulaConstant.is_active == True  # noqa: E712
        ).first()

    def get_all_active(self):
        return self.session.query(FormulaConstant).filter(
            FormulaConstant.is_active == True  # noqa: E712
        ).all()

    def get_constants_dict(self):
        """Return all active constants as {name: value} dict."""
        rows = self.get_all_active()
        return {r.name: r.value for r in rows}


class GammaConstantRepository(BaseRepository[GammaConstant]):
    def __init__(self, session=None):
        super().__init__(GammaConstant, session)

    def get_gamma(self, format_str: str, plug_length: int, condition: bool):
        """Lookup gamma value by format, plug_length and condition flag."""
        return self.session.query(GammaConstant).filter(
            GammaConstant.format == format_str,
            GammaConstant.plug_length == plug_length,
            GammaConstant.condition == condition,
            GammaConstant.is_active == True  # noqa: E712
        ).first()
