"""
Rules / governance engine – validates business rules before state changes.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Single validation failure."""
    field: str
    message: str
    code: str = 'INVALID'


@dataclass
class ValidationResult:
    """Aggregated validation outcome."""
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, field_name: str, message: str, code: str = 'INVALID'):
        self.errors.append(ValidationError(field=field_name, message=message, code=code))

    def to_dict(self) -> dict:
        return {
            'valid': self.is_valid,
            'errors': [{'field': e.field, 'message': e.message, 'code': e.code} for e in self.errors],
        }


class BaseRule:
    """Abstract base for all business rules."""

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        raise NotImplementedError


class MandatoryFieldsRule(BaseRule):
    """Validates that required fields are present and non-empty."""

    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        result = ValidationResult()
        for f in self.required_fields:
            val = data.get(f)
            if val is None or (isinstance(val, str) and not val.strip()):
                result.add_error(f, f'{f} is required', 'REQUIRED')
        return result


class ValueRangeRule(BaseRule):
    """Validates that numeric fields are within acceptable ranges."""

    def __init__(self, ranges: dict):
        # ranges = {'field_name': (min, max), ...}
        self.ranges = ranges

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        result = ValidationResult()
        for f, (min_val, max_val) in self.ranges.items():
            val = data.get(f)
            if val is not None:
                try:
                    val = float(val)
                    if min_val is not None and val < min_val:
                        result.add_error(f, f'{f} must be >= {min_val}', 'RANGE')
                    if max_val is not None and val > max_val:
                        result.add_error(f, f'{f} must be <= {max_val}', 'RANGE')
                except (ValueError, TypeError):
                    result.add_error(f, f'{f} must be a number', 'TYPE')
        return result


class StatusTransitionRule(BaseRule):
    """Validates that a status transition is allowed."""

    def __init__(self, transitions: dict):
        # transitions = {current_status: [allowed_next_statuses]}
        self.transitions = transitions

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        result = ValidationResult()
        current = data.get('current_status')
        target = data.get('target_status')
        if current and target:
            allowed = self.transitions.get(current, [])
            if target not in allowed:
                result.add_error(
                    'status',
                    f'Cannot transition from {current} to {target}. '
                    f'Allowed: {", ".join(str(s) for s in allowed)}',
                    'TRANSITION',
                )
        return result


class DuplicateCheckRule(BaseRule):
    """Checks for duplicate records using a repository lookup."""

    def __init__(self, repository, unique_field: str, entity_name: str = 'Record'):
        self.repository = repository
        self.unique_field = unique_field
        self.entity_name = entity_name

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        result = ValidationResult()
        value = data.get(self.unique_field)
        if value:
            existing = self.repository.exists({self.unique_field: value})
            if existing:
                result.add_error(
                    self.unique_field,
                    f'{self.entity_name} with {self.unique_field} "{value}" already exists',
                    'DUPLICATE',
                )
        return result


class RulesEngine:
    """Runs a sequence of rules and aggregates results."""

    def __init__(self, rules: Optional[List[BaseRule]] = None):
        self.rules = rules or []

    def add_rule(self, rule: BaseRule):
        self.rules.append(rule)

    def validate(self, data: dict, context: Optional[dict] = None) -> ValidationResult:
        combined = ValidationResult()
        for rule in self.rules:
            result = rule.validate(data, context)
            combined.errors.extend(result.errors)
        return combined
