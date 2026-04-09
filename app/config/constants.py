"""
Application-wide constants and enumerations.
"""
from enum import Enum


# ── Process Order Statuses ────────────────────────────────────────────────────
class ProcessOrderStatus(str, Enum):
    DRAFT = 'Draft'
    CALCULATED = 'Calculated'
    QA_PENDING = 'QA Pending'
    QA_UPDATED = 'QA Updated'
    COMPLETED = 'Completed'
    REPORT_GENERATED = 'Report Generated'

    # Valid transitions: {current_status: [allowed_next_statuses]}
    @classmethod
    def allowed_transitions(cls):
        return {
            cls.DRAFT: [cls.CALCULATED],
            cls.CALCULATED: [cls.QA_PENDING],
            cls.QA_PENDING: [cls.QA_UPDATED],
            cls.QA_UPDATED: [cls.COMPLETED],
            cls.COMPLETED: [cls.REPORT_GENERATED],
            cls.REPORT_GENERATED: [],
        }


# ── Product Development Statuses ─────────────────────────────────────────────
class ProductStatus(str, Enum):
    DRAFT = 'Draft'
    REVIEW = 'Review'
    APPROVED = 'Approved'
    RETIRED = 'Retired'

    @classmethod
    def allowed_transitions(cls):
        return {
            cls.DRAFT: [cls.REVIEW],
            cls.REVIEW: [cls.APPROVED, cls.DRAFT],
            cls.APPROVED: [cls.RETIRED],
            cls.RETIRED: [],
        }


# ── Batch Job Statuses ───────────────────────────────────────────────────────
class BatchJobStatus(str, Enum):
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    COMPLETED_WITH_ERRORS = 'Completed with Errors'
    FAILED = 'Failed'


class BatchJobItemStatus(str, Enum):
    PENDING = 'Pending'
    PROCESSING = 'Processing'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    SKIPPED = 'Skipped'


# ── Batch Job Types ──────────────────────────────────────────────────────────
class BatchJobType(str, Enum):
    QA_REPORT = 'qa_report'
    NPL_CALCULATION = 'npl_calculation'
    OPTIMIZER = 'optimizer'


# ── Audit Actions ────────────────────────────────────────────────────────────
class AuditAction(str, Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    VIEW = 'VIEW'
    CALCULATE = 'CALCULATE'
    OPTIMIZE = 'OPTIMIZE'
    APPROVE = 'APPROVE'
    REJECT = 'REJECT'
    EXPORT = 'EXPORT'
    IMPORT = 'IMPORT'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    STATUS_CHANGE = 'STATUS_CHANGE'
    GENERATE_REPORT = 'GENERATE_REPORT'


# ── Optimizer Methods ────────────────────────────────────────────────────────
class OptimizerMethod(str, Enum):
    INCREMENT = 'increment'
    MANUAL_ADJUSTMENT = 'manual_adjustment'
    DIRECT_WEIGHT = 'direct_weight'


# ── Permission Codes for cGR8s ───────────────────────────────────────────────
class Permissions(str, Enum):
    # Dashboard
    DASHBOARD_VIEW = 'DASHBOARD.VIEW'

    # FG Codes / SKU
    FG_CODE_VIEW = 'FG_CODE.VIEW'
    FG_CODE_CREATE = 'FG_CODE.CREATE'
    FG_CODE_EDIT = 'FG_CODE.EDIT'
    FG_CODE_DELETE = 'FG_CODE.DELETE'

    # Master Data
    MASTER_DATA_VIEW = 'MASTER_DATA.VIEW'
    MASTER_DATA_EDIT = 'MASTER_DATA.EDIT'

    # Master Data Sub-Pages
    MASTER_DATA_BLENDS = 'MASTER_DATA.BLENDS'
    MASTER_DATA_MACHINES = 'MASTER_DATA.MACHINES'
    MASTER_DATA_SKUS = 'MASTER_DATA.SKUS'
    MASTER_DATA_TOBACCO_ANALYSIS = 'MASTER_DATA.TOBACCO_ANALYSIS'
    MASTER_DATA_TARGETS_LIMITS = 'MASTER_DATA.TARGETS_LIMITS'
    MASTER_DATA_SIZE_CU = 'MASTER_DATA.SIZE_CU'
    MASTER_DATA_KP_TOLERANCE = 'MASTER_DATA.KP_TOLERANCE'
    MASTER_DATA_PLUG_LENGTH = 'MASTER_DATA.PLUG_LENGTH'
    MASTER_DATA_APP_FIELDS = 'MASTER_DATA.APP_FIELDS'
    MASTER_DATA_LOOKUPS = 'MASTER_DATA.LOOKUPS'
    MASTER_DATA_CALIBRATION = 'MASTER_DATA.CALIBRATION'
    MASTER_DATA_FORMULA_CONSTANTS = 'MASTER_DATA.FORMULA_CONSTANTS'
    MASTER_DATA_GAMMA_CONSTANTS = 'MASTER_DATA.GAMMA_CONSTANTS'

    # Target Weight
    TARGET_WEIGHT_VIEW = 'TARGET_WEIGHT.VIEW'
    TARGET_WEIGHT_CALCULATE = 'TARGET_WEIGHT.CALCULATE'
    TARGET_WEIGHT_EXPORT = 'TARGET_WEIGHT.EXPORT'

    # Process Orders
    PROCESS_ORDER_VIEW = 'PROCESS_ORDER.VIEW'
    PROCESS_ORDER_CREATE = 'PROCESS_ORDER.CREATE'
    PROCESS_ORDER_EDIT = 'PROCESS_ORDER.EDIT'
    PROCESS_ORDER_DELETE = 'PROCESS_ORDER.DELETE'

    # NPL
    NPL_VIEW = 'NPL.VIEW'
    NPL_CALCULATE = 'NPL.CALCULATE'
    NPL_EXPORT = 'NPL.EXPORT'

    # QA
    QA_VIEW = 'QA.VIEW'
    QA_ENTER = 'QA.ENTER'
    QA_APPROVE = 'QA.APPROVE'

    # Optimizer
    OPTIMIZER_VIEW = 'OPTIMIZER.VIEW'
    OPTIMIZER_RUN = 'OPTIMIZER.RUN'
    OPTIMIZER_EXPORT = 'OPTIMIZER.EXPORT'

    # Batch
    BATCH_VIEW = 'BATCH.VIEW'
    BATCH_SUBMIT = 'BATCH.SUBMIT'

    # Reports
    REPORT_VIEW = 'REPORT.VIEW'
    REPORT_GENERATE = 'REPORT.GENERATE'
    REPORT_DOWNLOAD = 'REPORT.DOWNLOAD'

    # Product Development
    PRODUCT_DEV_VIEW = 'PRODUCT_DEV.VIEW'
    PRODUCT_DEV_CREATE = 'PRODUCT_DEV.CREATE'
    PRODUCT_DEV_UPDATE = 'PRODUCT_DEV.UPDATE'
    PRODUCT_DEV_APPROVE = 'PRODUCT_DEV.APPROVE'

    # Admin
    ADMIN_PANEL = 'ADMIN.PANEL'
    ADMIN_SETTINGS = 'ADMIN.SETTINGS'
    ADMIN_USERS = 'ADMIN.USERS'
    ADMIN_MASTERS = 'ADMIN.MASTERS'
    AUDIT_LOG_VIEW = 'AUDIT_LOG.VIEW'
