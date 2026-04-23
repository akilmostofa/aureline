"""registration profiles and recordings

Revision ID: d9f1a2b3c4d5
Revises: c4d5e6f7a8b9
Create Date: 2026-04-11 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd9f1a2b3c4d5'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('student_profile') as batch_op:
        batch_op.add_column(sa.Column('guardian_occupation', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('student_photo_path', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('student_photo_filename', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('guardian_photo_path', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('guardian_photo_filename', sa.String(length=255), nullable=True))

    with op.batch_alter_table('teacher_profile') as batch_op:
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('teacher_photo_path', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('teacher_photo_filename', sa.String(length=255), nullable=True))

    op.create_table(
        'recorded_class_video',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('class_name', sa.String(length=50), nullable=False),
        sa.Column('subject_label', sa.String(length=120), nullable=False),
        sa.Column('zoom_meeting_id', sa.String(length=120), nullable=True),
        sa.Column('recording_date', sa.Date(), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=30), nullable=False, server_default='zoom'),
        sa.Column('access_scope', sa.String(length=20), nullable=False, server_default='class_only'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['course.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.execute("UPDATE student_profile SET guardian_name='Guardian Pending' WHERE guardian_name IS NULL OR guardian_name='' ")
    op.execute("UPDATE student_profile SET address='Address pending update' WHERE address IS NULL OR address='' ")
    op.execute("UPDATE teacher_profile SET address='Address pending update' WHERE address IS NULL OR address='' ")

    with op.batch_alter_table('student_profile') as batch_op:
        batch_op.alter_column('guardian_name', existing_type=sa.String(length=120), nullable=False)
        batch_op.alter_column('address', existing_type=sa.Text(), nullable=False)

    with op.batch_alter_table('teacher_profile') as batch_op:
        batch_op.alter_column('address', existing_type=sa.Text(), nullable=False)


def downgrade():
    op.drop_table('recorded_class_video')
    with op.batch_alter_table('teacher_profile') as batch_op:
        batch_op.drop_column('teacher_photo_filename')
        batch_op.drop_column('teacher_photo_path')
        batch_op.drop_column('address')

    with op.batch_alter_table('student_profile') as batch_op:
        batch_op.drop_column('guardian_photo_filename')
        batch_op.drop_column('guardian_photo_path')
        batch_op.drop_column('student_photo_filename')
        batch_op.drop_column('student_photo_path')
        batch_op.drop_column('guardian_occupation')
