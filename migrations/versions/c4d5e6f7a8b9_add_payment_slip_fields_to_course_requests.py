"""add payment slip fields to course requests

Revision ID: c4d5e6f7a8b9
Revises: 7d323b243a83
Create Date: 2026-04-11 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = '7d323b243a83'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('course_request') as batch_op:
        batch_op.add_column(sa.Column('payment_slip_path', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('payment_slip_filename', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('payment_slip_uploaded_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('course_request') as batch_op:
        batch_op.drop_column('payment_slip_uploaded_at')
        batch_op.drop_column('payment_slip_filename')
        batch_op.drop_column('payment_slip_path')
