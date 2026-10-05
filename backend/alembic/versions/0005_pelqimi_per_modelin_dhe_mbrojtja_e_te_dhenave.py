"""pëlqimi për modelin gjuhësor dhe vendimi i portës së çidentifikimit (ADR 0019)

Rishikimi: 0005
Paraardhësi: 0004

Dokumentet që ekzistonin para këtij migrimi shënohen pa pëlqim: u ngarkuan kur nuk kishte pyetje, dhe nuk është
e vërtetë të thuhet se pacienti e dha. Pëlqimi vlen vetëm për përpunimet e ardhshme; dokumentet e vjetra nuk
përpunohen sërish.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('documents') as batch:
        batch.add_column(sa.Column('model_consent', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.add_column(sa.Column('model_consent_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('model_use', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('model_gate_kinds', sa.String(length=200), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('documents') as batch:
        batch.drop_column('model_gate_kinds')
        batch.drop_column('model_use')
        batch.drop_column('model_consent_at')
        batch.drop_column('model_consent')
