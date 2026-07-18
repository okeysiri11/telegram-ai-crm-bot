# Pagination contracts (frozen v1).

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @classmethod
    def from_query(cls, query: dict[str, str], *, default_page_size: int = 50) -> PaginationParams:
        page = int(query.get("page", "1") or "1")
        page_size = int(query.get("page_size", query.get("limit", str(default_page_size))) or default_page_size)
        return cls(page=max(page, 1), page_size=min(max(page_size, 1), 500))


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    has_next: bool

    @classmethod
    def build(cls, *, page: int, page_size: int, total: int) -> PaginationMeta:
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            has_next=(page * page_size) < total,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
