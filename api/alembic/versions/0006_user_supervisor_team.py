"""add supervisor role and team field

Revision ID: 0006_user_supervisor_team
Revises: 0005_invoice_type
Create Date: 2026-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_user_supervisor_team"
down_revision = "0005_invoice_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'supervisor'")
    op.add_column("users", sa.Column("team", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "team")
