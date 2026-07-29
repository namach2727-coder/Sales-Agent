"""Minimal shared SQLAlchemy repository helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base


ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Provide persistence helpers without owning a transaction."""

    def __init__(self, session: Session, model_type: type[ModelT]) -> None:
        self.session = session
        self.model_type = model_type

    def get_by_id(self, entity_id: int) -> ModelT | None:
        return self.session.scalar(
            select(self.model_type).where(self.model_type.id == entity_id)
        )

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)

    def flush(self) -> None:
        self.session.flush()

    def refresh(self, entity: ModelT) -> ModelT:
        self.session.refresh(entity)
        return entity
