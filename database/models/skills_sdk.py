"""AI Skills & SDK ORM — Sprint 36.8."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class SkillRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("skill_key", name="uq_skills_skill_key"),
        Index("ix_skills_category", "category"),
        Index("ix_skills_visibility", "visibility"),
    )

    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="analysis")
    latest_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="enterprise")
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    signature: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    author: Mapped[str] = mapped_column(String(128), nullable=False, default="platform")
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ratings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changelog_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class SkillVersionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skill_versions"
    __table_args__ = (
        Index("ix_skill_versions_skill_key", "skill_key"),
        UniqueConstraint("skill_key", "semver", name="uq_skill_versions_skill_semver"),
    )

    version_key: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[str] = mapped_column(String(32), nullable=False)
    changelog: Mapped[str] = mapped_column(Text, nullable=False, default="")
    signature: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    manifest_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class SkillDependencyRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skill_dependencies"
    __table_args__ = (Index("ix_skill_dependencies_skill_key", "skill_key"),)

    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    depends_on_key: Mapped[str] = mapped_column(String(128), nullable=False)
    constraint_kind: Mapped[str] = mapped_column(String(64), nullable=False, default="required")


class SkillPermissionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skill_permissions"
    __table_args__ = (Index("ix_skill_permissions_skill_key", "skill_key"),)

    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    permission: Mapped[str] = mapped_column(String(128), nullable=False)
    principal: Mapped[str | None] = mapped_column(String(128), nullable=True)


class InstalledSkillRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "installed_skills"
    __table_args__ = (
        UniqueConstraint("skill_key", "principal", name="uq_installed_skills_skill_principal"),
        Index("ix_installed_skills_state", "state"),
    )

    install_key: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="enabled")
    principal: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    sandbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resource_limits_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class SkillStatisticsRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skill_statistics"
    __table_args__ = (Index("ix_skill_statistics_metric_key", "metric_key"),)

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SkillMarketplaceRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "skill_marketplace"
    __table_args__ = (
        UniqueConstraint("skill_key", name="uq_skill_marketplace_skill_key"),
        Index("ix_skill_marketplace_repository", "repository"),
    )

    listing_key: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_key: Mapped[str] = mapped_column(String(128), nullable=False)
    repository: Mapped[str] = mapped_column(String(32), nullable=False, default="enterprise")
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    downloads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
