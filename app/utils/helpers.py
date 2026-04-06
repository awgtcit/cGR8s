"""Utility helpers – flash messages, pagination, formatters."""
from math import ceil
from datetime import datetime
from flask import flash


def flash_success(msg: str):
    flash(msg, 'success')


def flash_error(msg: str):
    flash(msg, 'danger')


def flash_warning(msg: str):
    flash(msg, 'warning')


def flash_info(msg: str):
    flash(msg, 'info')


def format_date(dt, fmt='%d %b %Y'):
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return ''


def format_number(val, decimals=4):
    if val is None:
        return ''
    return f'{float(val):,.{decimals}f}'


def paginate_args(request_args, default_per_page=25):
    """Extract page/per_page from request args."""
    page = max(1, int(request_args.get('page', 1)))
    per_page = min(100, max(1, int(request_args.get('per_page', default_per_page))))
    return page, per_page


class Pagination:
    """Simple pagination metadata."""

    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = ceil(total / per_page) if per_page else 1
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None
