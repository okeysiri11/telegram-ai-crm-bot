"""AUTO 1.6 document templates / metadata (additive to AUTO 1.5).

Revision ID: p5k678901234
Revises: o4j567890123
Create Date: 2026-08-19 11:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "p5k678901234"
down_revision: Union[str, None] = "o4j567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    def _has_col(table: str, col: str) -> bool:
        return (
            conn.exec_driver_sql(
                "SELECT 1 FROM information_schema.columns "
                f"WHERE table_schema = 'public' AND table_name = '{table}' AND column_name = '{col}'"
            ).scalar()
            is not None
        )

    if _exists("auto_ops_clients") and not _has_col("auto_ops_clients", "representative"):
        op.add_column("auto_ops_clients", sa.Column("representative", sa.String(256), nullable=True))

    doc_cols = [
        ("workflow_status", sa.Column("workflow_status", sa.String(32), nullable=True)),
        ("signature_status", sa.Column("signature_status", sa.String(32), nullable=True)),
        ("document_number", sa.Column("document_number", sa.String(128), nullable=True)),
        ("issued_by", sa.Column("issued_by", sa.String(256), nullable=True)),
        ("issued_date", sa.Column("issued_date", sa.String(32), nullable=True)),
        ("valid_until", sa.Column("valid_until", sa.String(32), nullable=True)),
        ("finance_verify", sa.Column("finance_verify", sa.String(32), nullable=True)),
        ("generated", sa.Column("generated", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("template_id", sa.Column("template_id", sa.String(64), nullable=True)),
        ("ocr_draft", sa.Column("ocr_draft", JSONB(), nullable=True)),
        ("extracted_vin", sa.Column("extracted_vin", sa.String(32), nullable=True)),
        ("source", sa.Column("source", sa.String(16), nullable=True)),
        ("assigned_to", sa.Column("assigned_to", sa.String(128), nullable=True)),
        ("category", sa.Column("category", sa.String(32), nullable=True)),
        ("legal_disclaimer", sa.Column("legal_disclaimer", sa.Text(), nullable=True)),
    ]
    if _exists("auto_ops_documents"):
        for name, col in doc_cols:
            if not _has_col("auto_ops_documents", name):
                op.add_column("auto_ops_documents", col)

    if not _exists("auto_ops_document_templates"):
        op.create_table(
            "auto_ops_document_templates",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("stage", sa.String(64), nullable=False, server_default="other"),
            sa.Column("stage_name", sa.String(128), nullable=True),
            sa.Column("document_type", sa.String(64), nullable=True),
            sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("configurable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_company", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("note_ru", sa.Text(), nullable=True),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_auto_ops_doc_tmpl_org", "auto_ops_document_templates", ["organization_id"])


def downgrade() -> None:
    pass
