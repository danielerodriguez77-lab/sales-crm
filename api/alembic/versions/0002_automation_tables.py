"""automation tables

Revision ID: 0002_automation_tables
Revises: 0001_initial
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0002_automation_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    taskstatus = pg.ENUM("open", "done", name="taskstatus", create_type=False)
    tasktype = pg.ENUM(
        "sla_first_contact",
        "stale_opportunity",
        "payment_due",
        "payment_overdue",
        name="tasktype",
        create_type=False,
    )
    alertscope = pg.ENUM("manager", "seller", "all", name="alertscope", create_type=False)
    alerttype = pg.ENUM(
        "sla_first_contact",
        "stale_opportunity",
        "payment_due",
        "payment_overdue",
        name="alerttype",
        create_type=False,
    )

    bind = op.get_bind()
    for enum_type in [taskstatus, tasktype, alertscope, alerttype]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", taskstatus, nullable=False, server_default="open"),
        sa.Column("task_type", tasktype, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("alert_type", alerttype, nullable=False),
        sa.Column("scope", alertscope, nullable=False),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("tasks")

    bind = op.get_bind()
    for enum_name in ["alerttype", "alertscope", "tasktype", "taskstatus"]:
        enum_type = sa.Enum(name=enum_name)
        enum_type.drop(bind, checkfirst=True)
