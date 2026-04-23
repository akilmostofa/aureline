"""add course fees and course requests

Revision ID: 7d323b243a83
Revises: 1c2a4d8f9b10
Create Date: 2026-04-11 08:08:47.819202

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d323b243a83'
down_revision = '1c2a4d8f9b10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'course_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_group', sa.String(length=50), nullable=False),
        sa.Column('requester_user_id', sa.Integer(), nullable=False),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('course_fee', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_provider', sa.String(length=30), nullable=False),
        sa.Column('payment_method', sa.String(length=30), nullable=False),
        sa.Column('transaction_ref', sa.String(length=120), nullable=False),
        sa.Column('payer_mobile', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('requested_for_name', sa.String(length=120), nullable=True),
        sa.Column('requested_class', sa.String(length=50), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id']),
        sa.ForeignKeyConstraint(['requester_user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['student_id'], ['student_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('course_request') as batch_op:
        batch_op.create_index(batch_op.f('ix_course_request_request_group'), ['request_group'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_request_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_course_request_transaction_ref'), ['transaction_ref'], unique=False)

    with op.batch_alter_table('course') as batch_op:
        batch_op.add_column(sa.Column('course_fee', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_open_for_enrollment', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('course') as batch_op:
        batch_op.drop_column('is_open_for_enrollment')
        batch_op.drop_column('course_fee')

    with op.batch_alter_table('course_request') as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_request_transaction_ref'))
        batch_op.drop_index(batch_op.f('ix_course_request_status'))
        batch_op.drop_index(batch_op.f('ix_course_request_request_group'))

    op.drop_table('course_request')
