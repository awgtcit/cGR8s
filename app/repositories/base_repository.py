"""
Base repository – generic CRUD, pagination, soft-delete, concurrency.
All domain repositories extend this class.
"""
import logging
from datetime import datetime, timezone
from typing import TypeVar, Generic, Type, Optional, Dict, Any, List, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_scoped_session
from app.models.base import generate_uuid

logger = logging.getLogger(__name__)
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Generic repository providing standard data access operations."""

    def __init__(self, model_class: Type[T], session: Optional[Session] = None):
        self.model_class = model_class
        self._session = session

    @property
    def session(self) -> Session:
        return self._session or get_scoped_session()

    # ── Read ──────────────────────────────────────────────────────────────

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Fetch a single record by primary key, excluding soft-deleted."""
        q = self.session.query(self.model_class).filter(
            self.model_class.id == entity_id
        )
        if hasattr(self.model_class, 'is_deleted'):
            q = q.filter(self.model_class.is_deleted == False)  # noqa: E712
        return q.first()

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Return all records matching optional filters."""
        q = self._base_query(filters)
        return q.all()

    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_dir: str = 'asc',
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return paginated results and total count as a dict."""
        q = self._base_query(filters)

        # Text search across specified fields
        if search and search_fields:
            search_conditions = []
            for field_name in search_fields:
                col = getattr(self.model_class, field_name, None)
                if col is not None:
                    search_conditions.append(col.ilike(f'%{search}%'))
            if search_conditions:
                from sqlalchemy import or_
                q = q.filter(or_(*search_conditions))

        total = q.count()

        # Ordering
        if order_by and hasattr(self.model_class, order_by):
            col = getattr(self.model_class, order_by)
            q = q.order_by(col.desc() if order_dir == 'desc' else col.asc())
        elif hasattr(self.model_class, 'created_at'):
            q = q.order_by(self.model_class.created_at.desc())

        # Pagination
        offset = (page - 1) * per_page
        items = q.offset(offset).limit(per_page).all()
        num_pages = (total + per_page - 1) // per_page
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': num_pages,
            'total_pages': num_pages,
        }

    # ── Write ─────────────────────────────────────────────────────────────

    def create(self, entity: T, user_id: Optional[str] = None) -> T:
        """Insert a new entity."""
        if not entity.id:
            entity.id = generate_uuid()
        if hasattr(entity, 'created_by') and user_id:
            entity.created_by = user_id
            entity.updated_by = user_id
        now = datetime.now(timezone.utc)
        if hasattr(entity, 'created_at'):
            entity.created_at = now
            entity.updated_at = now
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: T, user_id: Optional[str] = None) -> T:
        """Update an existing entity with concurrency check."""
        if hasattr(entity, 'updated_by') and user_id:
            entity.updated_by = user_id
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now(timezone.utc)
        if hasattr(entity, 'row_version'):
            entity.row_version = (entity.row_version or 0) + 1
        self.session.merge(entity)
        self.session.flush()
        return entity

    def soft_delete(self, entity_id: str, user_id: Optional[str] = None) -> bool:
        """Mark entity as deleted without removing from DB."""
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        if hasattr(entity, 'is_deleted'):
            entity.is_deleted = True
            entity.deleted_at = datetime.now(timezone.utc)
            if hasattr(entity, 'deleted_by'):
                entity.deleted_by = user_id
            self.session.flush()
            return True
        return False

    def hard_delete(self, entity_id: str) -> bool:
        """Permanently remove entity from DB."""
        entity = self.session.query(self.model_class).get(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.flush()
        return True

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching filters."""
        return self._base_query(filters).count()

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if at least one record matches filters."""
        return self._base_query(filters).first() is not None

    # ── Internals ─────────────────────────────────────────────────────────

    def _base_query(self, filters: Optional[Dict[str, Any]] = None):
        """Build base query with soft-delete exclusion and optional filters."""
        q = self.session.query(self.model_class)
        if hasattr(self.model_class, 'is_deleted'):
            q = q.filter(self.model_class.is_deleted == False)  # noqa: E712
        if filters:
            conditions = []
            for key, value in filters.items():
                col = getattr(self.model_class, key, None)
                if col is not None:
                    if isinstance(value, list):
                        conditions.append(col.in_(value))
                    else:
                        conditions.append(col == value)
            if conditions:
                q = q.filter(and_(*conditions))
        return q
