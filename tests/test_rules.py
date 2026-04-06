"""Tests for validation rules engine."""
from app.rules import (
    RulesEngine, MandatoryFieldsRule, ValueRangeRule,
    StatusTransitionRule, DuplicateCheckRule, ValidationResult,
)


class TestMandatoryFieldsRule:
    def test_all_present(self):
        rule = MandatoryFieldsRule(['name', 'code'])
        result = rule.validate({'name': 'A', 'code': 'B'})
        assert result.is_valid

    def test_missing_field(self):
        rule = MandatoryFieldsRule(['name', 'code'])
        result = rule.validate({'name': 'A'})
        assert not result.is_valid
        assert len(result.errors) == 1

    def test_empty_string(self):
        rule = MandatoryFieldsRule(['name'])
        result = rule.validate({'name': ''})
        assert not result.is_valid


class TestValueRangeRule:
    def test_within_range(self):
        rule = ValueRangeRule('count', 1, 100)
        result = rule.validate({'count': 50})
        assert result.is_valid

    def test_below_range(self):
        rule = ValueRangeRule('count', 1, 100)
        result = rule.validate({'count': 0})
        assert not result.is_valid

    def test_above_range(self):
        rule = ValueRangeRule('count', 1, 100)
        result = rule.validate({'count': 101})
        assert not result.is_valid

    def test_missing_field_skipped(self):
        rule = ValueRangeRule('count', 1, 100)
        result = rule.validate({})
        assert result.is_valid


class TestStatusTransitionRule:
    def test_valid_transition(self):
        transitions = {'Draft': ['Calculated'], 'Calculated': ['QA Pending']}
        rule = StatusTransitionRule(transitions)
        result = rule.validate({'current_status': 'Draft', 'new_status': 'Calculated'})
        assert result.is_valid

    def test_invalid_transition(self):
        transitions = {'Draft': ['Calculated'], 'Calculated': ['QA Pending']}
        rule = StatusTransitionRule(transitions)
        result = rule.validate({'current_status': 'Draft', 'new_status': 'QA Pending'})
        assert not result.is_valid


class TestRulesEngine:
    def test_all_pass(self):
        engine = RulesEngine()
        engine.add_rule(MandatoryFieldsRule(['name']))
        engine.add_rule(ValueRangeRule('count', 0, 10))
        result = engine.validate({'name': 'A', 'count': 5})
        assert result.is_valid

    def test_mixed_fail(self):
        engine = RulesEngine()
        engine.add_rule(MandatoryFieldsRule(['name']))
        engine.add_rule(ValueRangeRule('count', 0, 10))
        result = engine.validate({'count': 20})
        assert not result.is_valid
        assert len(result.errors) >= 2
