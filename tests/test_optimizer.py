"""Tests for Product Run Optimizer service."""
from app.services.optimizer import ProductRunOptimizer, OptimizerInput


class TestProductRunOptimizer:
    def setup_method(self):
        self.opt = ProductRunOptimizer()

    def test_optimize_adjustment(self):
        inp = OptimizerInput(
            process_order_id='test-po',
            fg_code='TEST001',
            method='adjustment',
            base_n_bld=0.72,
            base_p_cu=0.05,
            base_t_vnt=0.03,
            base_f_pd=120.0,
            base_m_ip=12.5,
            adjustment_n_bld=0.001,
            adjustment_p_cu=0.0,
            adjustment_t_vnt=0.0,
            adjustment_f_pd=0.0,
            adjustment_m_ip=0.0,
        )
        result = self.opt.optimize(inp, limits=[])
        assert result is not None
        assert result.optimized_cigarette_weight > 0
        assert result.optimized_tobacco_weight > 0

    def test_optimize_direct(self):
        inp = OptimizerInput(
            process_order_id='test-po',
            fg_code='TEST001',
            method='direct',
            base_n_bld=0.72,
            base_p_cu=0.05,
            base_t_vnt=0.03,
            base_f_pd=120.0,
            base_m_ip=12.5,
            target_n_bld=0.73,
            target_p_cu=0.05,
            target_t_vnt=0.03,
        )
        result = self.opt.optimize(inp, limits=[])
        assert result is not None

    def test_tolerance_check(self):
        limits = [
            {'parameter_name': 'n_bld', 'min_value': 0.70, 'max_value': 0.75},
            {'parameter_name': 'p_cu', 'min_value': 0.04, 'max_value': 0.06},
        ]
        inp = OptimizerInput(
            process_order_id='test-po',
            fg_code='TEST001',
            method='adjustment',
            base_n_bld=0.72,
            base_p_cu=0.05,
            base_t_vnt=0.03,
            base_f_pd=120.0,
            base_m_ip=12.5,
            adjustment_n_bld=0.01,
        )
        result = self.opt.optimize(inp, limits=limits)
        assert result is not None
        assert isinstance(result.within_tolerance, bool)
