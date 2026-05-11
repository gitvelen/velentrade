"""add approval record payload fields

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260503_0003"
down_revision = "20260503_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("approval_record", sa.Column("comparison_options", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("approval_record", sa.Column("risk_and_impact", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("approval_record", sa.Column("timeout_policy", sa.String(), nullable=True))
    op.execute("UPDATE approval_record SET comparison_options = '[]'::jsonb WHERE comparison_options IS NULL")
    op.execute("UPDATE approval_record SET risk_and_impact = '{}'::jsonb WHERE risk_and_impact IS NULL")
    op.execute("UPDATE approval_record SET timeout_policy = 'timeout_means_no_execution' WHERE timeout_policy IS NULL")
    op.alter_column("approval_record", "comparison_options", nullable=False)
    op.alter_column("approval_record", "risk_and_impact", nullable=False)
    op.alter_column("approval_record", "timeout_policy", nullable=False)


def downgrade() -> None:
    op.drop_column("approval_record", "timeout_policy")
    op.drop_column("approval_record", "risk_and_impact")
    op.drop_column("approval_record", "comparison_options")
