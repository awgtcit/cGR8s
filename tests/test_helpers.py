"""Tests for utility helpers."""
from app.utils.helpers import Pagination


class TestPagination:
    def test_single_page(self):
        p = Pagination(page=1, per_page=10, total=5)
        assert p.pages == 1
        assert not p.has_prev
        assert not p.has_next

    def test_multi_page(self):
        p = Pagination(page=2, per_page=10, total=25)
        assert p.pages == 3
        assert p.has_prev
        assert p.has_next

    def test_last_page(self):
        p = Pagination(page=3, per_page=10, total=25)
        assert p.has_prev
        assert not p.has_next

    def test_zero_total(self):
        p = Pagination(page=1, per_page=10, total=0)
        assert p.pages == 0
        assert not p.has_prev
        assert not p.has_next
