"""risk_engine_v1

Revision ID: bfdac8a7c0bd
Revises: d85e4567bcf9
Create Date: 2026-07-12 18:14:20.428314

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "bfdac8a7c0bd"
down_revision: Union[str, None] = "d85e4567bcf9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("risk.detected", "Emit or subscribe to risk detected events"),
    ("risk.review_required", "Emit or subscribe to risk review required events"),
    ("risk.approved", "Emit or subscribe to risk approved events"),
    ("risk.rejected", "Emit or subscribe to risk rejected events"),
    ("risk.override", "Emit or subscribe to risk override events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "LAWYER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ACCOUNTANT": frozenset(
        {"risk.detected", "risk.review_required", "risk.approved", "risk.rejected"}
    ),
}

DEFAULT_RULES: tuple[tuple[str, str, str, str, str | None, dict | None], ...] = (
    (
        "deal.amount.high",
        "TRANSACTION_RISK",
        "HIGH",
        "100000",
        "Deal amount above 100k requires review",
        None,
    ),
    (
        "deal.amount.critical",
        "TRANSACTION_RISK",
        "CRITICAL",
        "500000",
        "Deal amount above 500k requires owner approval",
        None,
    ),
    (
        "kyc.amount.l2",
        "KYC_RISK",
        "HIGH",
        "50000",
        "Amounts above 50k require KYC L2",
        {"min_level": "L2"},
    ),
    (
        "kyc.amount.l3",
        "KYC_RISK",
        "HIGH",
        "250000",
        "Amounts above 250k require KYC L3",
        {"min_level": "L3"},
    ),
    (
        "country.blocked",
        "COUNTRY_RISK",
        "CRITICAL",
        None,
        "Blocked jurisdictions",
        {"blocked_countries": ["KP", "IR", "SY", "CU"]},
    ),
)

DEFAULT_EXPOSURE_LIMITS: tuple[tuple[str, str | None, str | None, str, str], ...] = (
    ("GLOBAL", None, None, "10000000", "Global platform exposure cap"),
    ("ASSET", "USDT", "USDT", "5000000", "USDT concentration limit"),
    ("ASSET", "USD", "USD", "5000000", "USD concentration limit"),
)


def _seed_risk_event_permissions() -> None:
    bind = op.get_bind()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in NEW_EVENT_PERMISSIONS:
        existing = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if existing:
            permission_ids[code] = existing[0]
            continue
        permission_id = uuid.uuid4()
        bind.execute(
            permissions_table.insert().values(
                id=permission_id,
                code=code,
                description=description,
            )
        )
        permission_ids[code] = permission_id

    for role_code, permission_codes in NEW_ROLE_PERMISSIONS.items():
        role_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": role_code},
        ).first()
        if not role_row:
            continue
        role_id = role_row[0]
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                perm_row = bind.execute(
                    sa.text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": permission_code},
                ).first()
                if not perm_row:
                    continue
                permission_id = perm_row[0]
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).first()
            if exists:
                continue
            bind.execute(
                role_permissions_table.insert().values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def _seed_default_rules() -> None:
    bind = op.get_bind()
    rules_table = sa.table(
        "risk_v1_rules",
        sa.column("id", sa.UUID()),
        sa.column("rule_code", sa.String()),
        sa.column("rule_type", sa.String()),
        sa.column("risk_level", sa.String()),
        sa.column("threshold", sa.Numeric()),
        sa.column("description", sa.Text()),
        sa.column("config", postgresql.JSONB()),
        sa.column("is_active", sa.Boolean()),
    )
    for rule_code, rule_type, risk_level, threshold, description, config in DEFAULT_RULES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM risk_v1_rules WHERE rule_code = :code"),
            {"code": rule_code},
        ).first()
        if exists:
            continue
        bind.execute(
            rules_table.insert().values(
                id=uuid.uuid4(),
                rule_code=rule_code,
                rule_type=rule_type,
                risk_level=risk_level,
                threshold=threshold,
                description=description,
                config=config,
                is_active=True,
            )
        )


def _seed_default_exposure_limits() -> None:
    bind = op.get_bind()
    limits_table = sa.table(
        "risk_v1_exposure_limits",
        sa.column("id", sa.UUID()),
        sa.column("scope", sa.String()),
        sa.column("scope_key", sa.String()),
        sa.column("asset", sa.String()),
        sa.column("max_exposure", sa.Numeric()),
        sa.column("current_exposure", sa.Numeric()),
        sa.column("description", sa.Text()),
        sa.column("is_active", sa.Boolean()),
    )
    for scope, scope_key, asset, max_exposure, description in DEFAULT_EXPOSURE_LIMITS:
        exists = bind.execute(
            sa.text(
                "SELECT 1 FROM risk_v1_exposure_limits "
                "WHERE scope = :scope AND scope_key IS NOT DISTINCT FROM :scope_key"
            ),
            {"scope": scope, "scope_key": scope_key},
        ).first()
        if exists:
            continue
        bind.execute(
            limits_table.insert().values(
                id=uuid.uuid4(),
                scope=scope,
                scope_key=scope_key,
                asset=asset,
                max_exposure=max_exposure,
                current_exposure="0",
                description=description,
                is_active=True,
            )
        )


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "risk_v1_exposure_limits",
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_key", sa.String(length=100), nullable=True),
        sa.Column("asset", sa.String(length=20), nullable=True),
        sa.Column("max_exposure", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("current_exposure", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_exposure >= 0",
            name="ck_risk_v1_exposure_limits_current",
        ),
        sa.CheckConstraint("max_exposure >= 0", name="ck_risk_v1_exposure_limits_max"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_v1_exposure_limits_is_active",
        "risk_v1_exposure_limits",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_exposure_limits_scope",
        "risk_v1_exposure_limits",
        ["scope"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_exposure_limits_scope_key",
        "risk_v1_exposure_limits",
        ["scope_key"],
        unique=False,
    )
    op.create_table(
        "risk_v1_rules",
        sa.Column("rule_code", sa.String(length=64), nullable=False),
        sa.Column("rule_type", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code"),
    )
    op.create_index("ix_risk_v1_rules_is_active", "risk_v1_rules", ["is_active"], unique=False)
    op.create_index("ix_risk_v1_rules_rule_code", "risk_v1_rules", ["rule_code"], unique=False)
    op.create_index("ix_risk_v1_rules_rule_type", "risk_v1_rules", ["rule_type"], unique=False)
    op.create_table(
        "risk_v1_decisions",
        sa.Column("evaluation_type", sa.String(length=20), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("asset", sa.String(length=20), nullable=True),
        sa.Column("amount", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("checks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decided_by", sa.BigInteger(), nullable=True),
        sa.Column("override_by", sa.BigInteger(), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("overridden_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_deals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["partner_engine_partners.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_v1_decisions_deal_id",
        "risk_v1_decisions",
        ["deal_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_decisions_decision",
        "risk_v1_decisions",
        ["decision"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_decisions_evaluation_type",
        "risk_v1_decisions",
        ["evaluation_type"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_decisions_partner_id",
        "risk_v1_decisions",
        ["partner_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_decisions_risk_level",
        "risk_v1_decisions",
        ["risk_level"],
        unique=False,
    )
    op.create_table(
        "risk_v1_events",
        sa.Column("rule_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=True),
        sa.Column("source_id", sa.String(length=100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_deals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["partner_engine_partners.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["rule_id"], ["risk_v1_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_v1_events_deal_id", "risk_v1_events", ["deal_id"], unique=False)
    op.create_index(
        "ix_risk_v1_events_partner_id",
        "risk_v1_events",
        ["partner_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_events_risk_level",
        "risk_v1_events",
        ["risk_level"],
        unique=False,
    )
    op.create_index("ix_risk_v1_events_rule_id", "risk_v1_events", ["rule_id"], unique=False)
    op.create_index("ix_risk_v1_events_status", "risk_v1_events", ["status"], unique=False)
    op.create_table(
        "risk_v1_blocked_operations",
        sa.Column("decision_id", sa.UUID(), nullable=False),
        sa.Column("operation_type", sa.String(length=40), nullable=False),
        sa.Column("subject_type", sa.String(length=40), nullable=False),
        sa.Column("subject_id", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rule_code", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["risk_v1_decisions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_v1_blocked_operations_decision_id",
        "risk_v1_blocked_operations",
        ["decision_id"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_blocked_operations_is_active",
        "risk_v1_blocked_operations",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_risk_v1_blocked_operations_operation_type",
        "risk_v1_blocked_operations",
        ["operation_type"],
        unique=False,
    )
    _seed_default_rules()
    _seed_default_exposure_limits()
    _seed_risk_event_permissions()
    # ### end Alembic commands ###


def downgrade() -> None:
    bind = op.get_bind()
    codes = [code for code, _ in NEW_EVENT_PERMISSIONS]
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions WHERE code = ANY(:codes))"
        ),
        {"codes": codes},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "ix_risk_v1_blocked_operations_operation_type",
        table_name="risk_v1_blocked_operations",
    )
    op.drop_index(
        "ix_risk_v1_blocked_operations_is_active",
        table_name="risk_v1_blocked_operations",
    )
    op.drop_index(
        "ix_risk_v1_blocked_operations_decision_id",
        table_name="risk_v1_blocked_operations",
    )
    op.drop_table("risk_v1_blocked_operations")
    op.drop_index("ix_risk_v1_events_status", table_name="risk_v1_events")
    op.drop_index("ix_risk_v1_events_rule_id", table_name="risk_v1_events")
    op.drop_index("ix_risk_v1_events_risk_level", table_name="risk_v1_events")
    op.drop_index("ix_risk_v1_events_partner_id", table_name="risk_v1_events")
    op.drop_index("ix_risk_v1_events_deal_id", table_name="risk_v1_events")
    op.drop_table("risk_v1_events")
    op.drop_index("ix_risk_v1_decisions_risk_level", table_name="risk_v1_decisions")
    op.drop_index("ix_risk_v1_decisions_partner_id", table_name="risk_v1_decisions")
    op.drop_index("ix_risk_v1_decisions_evaluation_type", table_name="risk_v1_decisions")
    op.drop_index("ix_risk_v1_decisions_decision", table_name="risk_v1_decisions")
    op.drop_index("ix_risk_v1_decisions_deal_id", table_name="risk_v1_decisions")
    op.drop_table("risk_v1_decisions")
    op.drop_index("ix_risk_v1_rules_rule_type", table_name="risk_v1_rules")
    op.drop_index("ix_risk_v1_rules_rule_code", table_name="risk_v1_rules")
    op.drop_index("ix_risk_v1_rules_is_active", table_name="risk_v1_rules")
    op.drop_table("risk_v1_rules")
    op.drop_index("ix_risk_v1_exposure_limits_scope_key", table_name="risk_v1_exposure_limits")
    op.drop_index("ix_risk_v1_exposure_limits_scope", table_name="risk_v1_exposure_limits")
    op.drop_index("ix_risk_v1_exposure_limits_is_active", table_name="risk_v1_exposure_limits")
    op.drop_table("risk_v1_exposure_limits")
    # ### end Alembic commands ###
