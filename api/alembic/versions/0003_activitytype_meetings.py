"""add activity meeting types

Revision ID: 0003_activitytype_meetings
Revises: 0002_automation_tables
Create Date: 2026-03-01
"""

from alembic import op

revision = "0003_activitytype_meetings"
down_revision = "0002_automation_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'reunion_online'")
    op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'reunion_presencial'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily.
    pass
