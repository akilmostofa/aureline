"""add user approval fields

Revision ID: 1c2a4d8f9b10
Revises: 63962d2ff6ef
Create Date: 2026-04-11 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '1c2a4d8f9b10'
down_revision = '63962d2ff6ef'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('approval_status', sa.String(length=20), nullable=False, server_default='approved'))
        batch_op.add_column(sa.Column('registration_source', sa.String(length=20), nullable=False, server_default='admin_created'))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('approved_by_user_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_approval_status'), ['approval_status'], unique=False)
        batch_op.create_foreign_key('fk_user_approved_by_user_id', 'user', ['approved_by_user_id'], ['id'])

    op.execute("UPDATE user SET approval_status='approved' WHERE approval_status IS NULL")
    op.execute("UPDATE user SET registration_source='seeded_demo' WHERE registration_source IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_approved_by_user_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_user_approval_status'))
        batch_op.drop_column('approved_by_user_id')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('registration_source')
        batch_op.drop_column('approval_status')
