"""add position disposal task mirror

Revision ID: 20260503_0004
Revises: 20260503_0003
Create Date: 2026-05-03 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260503_0004"
down_revision = "20260503_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "position_disposal_task",
        sa.Column("task_id", sa.String(), primary_key=True),
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("workflow_id", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("triggers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("risk_gate_present", sa.Boolean(), nullable=False),
        sa.Column("execution_core_guard_present", sa.Boolean(), nullable=False),
        sa.Column("direct_execution_allowed", sa.Boolean(), nullable=False),
        sa.Column("workflow_route", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("position_disposal_task")
