"""rivendosja e fjalëkalimit, hapi i dytë (TOTP) dhe regjistri i dërgimit të email-eve (ADR 0018)

Rishikimi: 0004
Paraardhësi: 0003

Llogaritë ekzistuese mbeten pa hap të dytë: `totp_enabled_at` është bosh derisa përdoruesi ta aktivizojë.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('totp_secret_encrypted', sa.LargeBinary(), nullable=True))
        batch.add_column(sa.Column('totp_enabled_at', sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('totp_last_step', sa.Integer(), nullable=True))

    op.create_table('password_resets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_key', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_token_key'), 'password_resets', ['token_key'], unique=True)
    op.create_index(op.f('ix_password_resets_user_id'), 'password_resets', ['user_id'], unique=False)
    op.create_table('recovery_codes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('code_key', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code_key')
    )
    op.create_index(op.f('ix_recovery_codes_user_id'), 'recovery_codes', ['user_id'], unique=False)
    op.create_table('mail_deliveries',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('token_id', sa.Uuid(), nullable=False),
    sa.Column('origin', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('last_error', sa.String(length=80), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mail_deliveries_status_created', 'mail_deliveries', ['status', 'created_at'], unique=False)
    op.create_index(op.f('ix_mail_deliveries_user_id'), 'mail_deliveries', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mail_deliveries_user_id'), table_name='mail_deliveries')
    op.drop_index('ix_mail_deliveries_status_created', table_name='mail_deliveries')
    op.drop_table('mail_deliveries')
    op.drop_index(op.f('ix_recovery_codes_user_id'), table_name='recovery_codes')
    op.drop_table('recovery_codes')
    op.drop_index(op.f('ix_password_resets_user_id'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_token_key'), table_name='password_resets')
    op.drop_table('password_resets')
    with op.batch_alter_table('users') as batch:
        batch.drop_column('totp_last_step')
        batch.drop_column('totp_enabled_at')
        batch.drop_column('totp_secret_encrypted')
