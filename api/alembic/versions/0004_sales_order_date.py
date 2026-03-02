"""add sales order date

Revision ID: 0004_sales_order_date
Revises: 0003_activitytype_meetings
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_sales_order_date"
down_revision = "0003_activitytype_meetings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sales_orders", sa.Column("order_date", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE sales_orders SET order_date = created_at WHERE order_date IS NULL")


def downgrade() -> None:
    op.drop_column("sales_orders", "order_date")
