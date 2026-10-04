"""konfirmimi i email-it dhe kufizimi i regjistrimeve (ADR 0016)

Rishikimi: 0003
Paraardhësi: 0002

Llogaritë që ekzistonin para këtij migrimi shënohen si të konfirmuara në çastin e krijimit të
tyre: ato u regjistruan kur shërbimi nuk dërgonte email, dhe të kërkohej konfirmim nga ato do t'i
mbyllte jashtë pa asnjë mënyrë për ta bërë atë.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('email_confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.execute('UPDATE users SET email_confirmed_at = created_at')

    op.create_table('email_confirmations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_key', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_confirmations_token_key'), 'email_confirmations', ['token_key'], unique=True)
    op.create_index(op.f('ix_email_confirmations_user_id'), 'email_confirmations', ['user_id'], unique=False)
    op.create_table('registration_attempts',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email_key', sa.String(length=64), nullable=False),
    sa.Column('ip_key', sa.String(length=64), nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_registration_attempts_email_at', 'registration_attempts', ['email_key', 'at'], unique=False)
    op.create_index('ix_registration_attempts_ip_at', 'registration_attempts', ['ip_key', 'at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_registration_attempts_ip_at', table_name='registration_attempts')
    op.drop_index('ix_registration_attempts_email_at', table_name='registration_attempts')
    op.drop_table('registration_attempts')
    op.drop_index(op.f('ix_email_confirmations_user_id'), table_name='email_confirmations')
    op.drop_index(op.f('ix_email_confirmations_token_key'), table_name='email_confirmations')
    op.drop_table('email_confirmations')
    with op.batch_alter_table('users') as batch:
        batch.drop_column('email_confirmed_at')
