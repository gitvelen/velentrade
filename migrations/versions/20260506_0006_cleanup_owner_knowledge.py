"""cleanup owner knowledge garbage rows

Revision ID: 20260506_0006
Revises: 20260506_0005
Create Date: 2026-05-06 10:20:00
"""
from __future__ import annotations

from alembic import op


revision = "20260506_0006"
down_revision = "20260506_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        delete from memory_relation
        where source_memory_id in (
            select mi.memory_id
            from memory_item mi
            left join memory_version mv on mv.version_id = mi.current_version_id
            left join memory_extraction_result mer on mer.memory_version_id = mv.version_id
            where lower(coalesce(mer.title, 'untitled memory')) in ('test', '测试', 'untitled memory')
               or lower(trim(coalesce(mv.content_markdown, ''))) in ('test', '测试')
               or coalesce(mi.sensitivity, '') not in ('public_internal', 'finance_sensitive_raw')
               or coalesce(mi.source_refs, '[]'::jsonb) = '[]'::jsonb
               or trim(coalesce(mv.content_markdown, '')) = ''
        )
           or target_ref = ''
           or relation_type = ''
           or reason = ''
           or coalesce(evidence_refs, '[]'::jsonb) = '[]'::jsonb
           or (
               target_ref = 'knowledge-method-1'
               and (
                   reason = 'Owner applied organize suggestion from Knowledge workspace'
                   or coalesce(evidence_refs, '[]'::jsonb) ? 'knowledge_memory_workspace'
               )
           )
        """
    )
    op.execute(
        """
        delete from memory_extraction_result
        where memory_version_id in (
            select mv.version_id
            from memory_item mi
            join memory_version mv on mv.version_id = mi.current_version_id
            left join memory_extraction_result mer on mer.memory_version_id = mv.version_id
            where lower(coalesce(mer.title, 'untitled memory')) in ('test', '测试', 'untitled memory')
               or lower(trim(coalesce(mv.content_markdown, ''))) in ('test', '测试')
               or coalesce(mi.sensitivity, '') not in ('public_internal', 'finance_sensitive_raw')
               or coalesce(mi.source_refs, '[]'::jsonb) = '[]'::jsonb
               or trim(coalesce(mv.content_markdown, '')) = ''
        )
        """
    )
    op.execute(
        """
        delete from memory_version
        where memory_id in (
            select mi.memory_id
            from memory_item mi
            left join memory_version mv on mv.version_id = mi.current_version_id
            left join memory_extraction_result mer on mer.memory_version_id = mv.version_id
            where lower(coalesce(mer.title, 'untitled memory')) in ('test', '测试', 'untitled memory')
               or lower(trim(coalesce(mv.content_markdown, ''))) in ('test', '测试')
               or coalesce(mi.sensitivity, '') not in ('public_internal', 'finance_sensitive_raw')
               or coalesce(mi.source_refs, '[]'::jsonb) = '[]'::jsonb
               or trim(coalesce(mv.content_markdown, '')) = ''
        )
        """
    )
    op.execute(
        """
        delete from memory_item
        where memory_id not in (select memory_id from memory_version)
           or lower(coalesce(sensitivity, '')) not in ('public_internal', 'finance_sensitive_raw')
           or coalesce(source_refs, '[]'::jsonb) = '[]'::jsonb
        """
    )


def downgrade() -> None:
    pass
