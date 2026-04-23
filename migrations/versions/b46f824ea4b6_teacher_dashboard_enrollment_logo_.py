"""teacher dashboard enrollment logo updates

Revision ID: b46f824ea4b6
Revises: 55ff59e994f6
Create Date: 2026-04-12 10:16:57.888933

"""
from alembic import op
import sqlalchemy as sa

revision = 'b46f824ea4b6'
down_revision = '55ff59e994f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delivery_status', sa.String(length=20), nullable=False, server_default='running'))
        batch_op.add_column(sa.Column('next_schedule_text', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('suspension_note', sa.Text(), nullable=True))

    with op.batch_alter_table('course_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enrollment_status', sa.String(length=20), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('admin_override_active', sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table('student_profile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_school_name', sa.String(length=150), nullable=True))


def downgrade():
    with op.batch_alter_table('student_profile', schema=None) as batch_op:
        batch_op.drop_column('current_school_name')

    with op.batch_alter_table('course_request', schema=None) as batch_op:
        batch_op.drop_column('admin_override_active')
        batch_op.drop_column('enrollment_status')

    with op.batch_alter_table('course', schema=None) as batch_op:
        batch_op.drop_column('suspension_note')
        batch_op.drop_column('next_schedule_text')
        batch_op.drop_column('delivery_status')
