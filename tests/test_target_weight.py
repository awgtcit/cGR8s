"""Tests for Target Weight Calculator service."""
from app.services.target_weight_calc import TargetWeightCalculator, TargetWeightInput


class TestTargetWeightCalculator:
    def setup_method(self):
        self.calc = TargetWeightCalculator()

    def test_calculate_returns_output(self):
        inp = TargetWeightInput(
            fg_code='TEST001',
            n_bld=0.7200,
            p_cu=0.0500,
            t_vnt=0.0300,
            f_pd=120.0,
            m_ip=12.5,
            cigarette_circumference=24.5,
            cigarette_length=84.0,
            filter_length=27.0,
            tipping_length=32.0,
            paper_weight=26.0,
            filter_weight=0.12,
            glue_weight=0.008,
        )
        output = self.calc.calculate(inp)
        assert output is not None
        assert output.cigarette_weight > 0
        assert output.tobacco_weight > 0
        assert output.target_weight > 0
        assert output.paper_weight_contribution >= 0

    def test_calculate_zero_circumference_raises(self):
        inp = TargetWeightInput(
            fg_code='TEST002',
            n_bld=0.72, p_cu=0.05, t_vnt=0.03, f_pd=120.0, m_ip=12.5,
            cigarette_circumference=0.0,
            cigarette_length=84.0, filter_length=27.0,
            tipping_length=32.0, paper_weight=26.0,
            filter_weight=0.12, glue_weight=0.008,
        )
        try:
            self.calc.calculate(inp)
            assert False, "Should have raised an error"
        except (ValueError, ZeroDivisionError):
            pass
