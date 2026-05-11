"""add finance profile persistence

Revision ID: 20260503_0002
Revises: 20260502_0001
Create Date: 2026-05-03 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260503_0002"
down_revision = "20260502_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_profile",
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("assets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("liabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cash_flow_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tax_reminder_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_budget", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("liquidity_constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sensitive_fields_encrypted", sa.Boolean(), nullable=False),
        sa.Column("derived_summary_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("manual_todos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("profile_id"),
    )


def downgrade() -> None:
    op.drop_table("finance_profile")
