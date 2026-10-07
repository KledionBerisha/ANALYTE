"""këshillat me burim për gjetjet jashtë intervalit (ADR 0023)

Rishikimi: 0006
Paraardhësi: 0005

Këshillat ruhen të plota krahas kontekstit, si fjalori: nëse rreshti i tabelës ndryshon më vonë, fjalia që pa
pacienti mbetet e gjurmueshme bashkë me burimin e saj. Dokumentet e vjetra nuk kanë rreshta këtu dhe nuk
përpunohen sërish.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'document_advice',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('finding_id', sa.Uuid(), nullable=False),
        sa.Column('analyte_code', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=20), nullable=False),
        sa.Column('advice_sq', sa.Text(), nullable=False),
        sa.Column('source_ref', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_advice_document_id'), 'document_advice', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_advice_document_id'), table_name='document_advice')
    op.drop_table('document_advice')
