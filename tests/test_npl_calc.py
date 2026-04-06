"""Tests for NPL Calculator service."""
from app.services.npl_calc import NPLCalculator, NPLInput


class TestNPLCalculator:
    def setup_method(self):
        self.calc = NPLCalculator()

    def test_calculate_basic(self):
        inp = NPLInput(
            process_order_id='test-po-id',
            fg_code='TEST001',
            planned_quantity=1000000,
            actual_output=980000,
            tobacco_input=5000.0,
            tobacco_waste=50.0,
            wrapping_input=200.0,
            wrapping_waste=5.0,
            filter_input=1010000,
            filter_waste=10000,
            packaging_input=50000,
            packaging_waste=500,
            opening_stock_tobacco=100.0,
            closing_stock_tobacco=80.0,
            opening_stock_wrapping=20.0,
            closing_stock_wrapping=15.0,
        )
        result = self.calc.calculate(inp)
        assert result is not None
        assert result.npl_percentage >= 0
        assert result.total_actual_consumption > 0
        assert result.total_theoretical_consumption > 0

    def test_calculate_zero_planned(self):
        inp = NPLInput(
            process_order_id='test-po-id',
            fg_code='TEST002',
            planned_quantity=0,
            actual_output=0,
            tobacco_input=0, tobacco_waste=0,
            wrapping_input=0, wrapping_waste=0,
            filter_input=0, filter_waste=0,
            packaging_input=0, packaging_waste=0,
            opening_stock_tobacco=0, closing_stock_tobacco=0,
            opening_stock_wrapping=0, closing_stock_wrapping=0,
        )
        result = self.calc.calculate(inp)
        assert result is not None
        assert result.npl_percentage == 0
