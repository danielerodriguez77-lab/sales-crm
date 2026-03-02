"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    userrole = pg.ENUM("seller", "manager", "admin", name="userrole", create_type=False)
    opportunitytype = pg.ENUM("lead", "opportunity", name="opportunitytype", create_type=False)
    pipelinestage = pg.ENUM(
        "lead_nuevo",
        "calificado",
        "contacto_seguimiento",
        "oferta_enviada",
        "negociacion",
        "ganado",
        "facturacion",
        "cobro_parcial",
        "pagado_cerrado",
        "perdido",
        name="pipelinestage",
        create_type=False,
    )
    activitytype = pg.ENUM(
        "call", "visit", "whatsapp", "email", "demo", "other", name="activitytype", create_type=False
    )
    quotestatus = pg.ENUM("draft", "sent", "accepted", "rejected", name="quotestatus", create_type=False)
    approvalstatus = pg.ENUM(
        "not_required", "pending", "approved", "rejected", name="approvalstatus", create_type=False
    )
    salesorderstatus = pg.ENUM(
        "open", "cancelled", "fulfilled", name="salesorderstatus", create_type=False
    )
    invoicestatus = pg.ENUM(
        "draft", "issued", "partial", "paid", "overdue", name="invoicestatus", create_type=False
    )
    paymentmethod = pg.ENUM(
        "cash", "transfer", "card", "check", "other", name="paymentmethod", create_type=False
    )

    bind = op.get_bind()
    for enum_type in [
        userrole,
        opportunitytype,
        pipelinestage,
        activitytype,
        quotestatus,
        approvalstatus,
        salesorderstatus,
        invoicestatus,
        paymentmethod,
    ]:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", userrole, nullable=False, server_default="seller"),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("payment_terms", sa.String(length=100), nullable=True),
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
        "opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("record_type", opportunitytype, nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("person_name", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("segment", sa.String(length=100), nullable=True),
        sa.Column("estimated_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("probability", sa.Integer(), nullable=True),
        sa.Column("stage", pipelinestage, nullable=False, server_default="lead_nuevo"),
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("no_next_action", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
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
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("activity_type", activitytype, nullable=False),
        sa.Column("activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
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
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id")),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("status", quotestatus, nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("items", sa.JSON(), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=True),
        sa.Column("tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("total", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("approval_status", approvalstatus, nullable=False, server_default="not_required"),
        sa.Column("pdf_path", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_quotes_number", "quotes", ["number"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)

    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey("opportunities.id")),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id")),
        sa.Column("status", salesorderstatus, nullable=False, server_default="open"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=True),
        sa.Column("tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("total", sa.Numeric(12, 2), nullable=True),
        sa.Column("reference", sa.String(length=100), nullable=True),
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
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sales_order_id", sa.Integer(), sa.ForeignKey("sales_orders.id")),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", invoicestatus, nullable=False, server_default="draft"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_invoices_number", "invoices", ["number"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id")),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("method", paymentmethod, nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("attachment_path", sa.String(length=255), nullable=True),
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
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("payments")
    op.drop_index("ix_invoices_number", table_name="invoices")
    op.drop_table("invoices")
    op.drop_table("sales_orders")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_quotes_number", table_name="quotes")
    op.drop_table("quotes")
    op.drop_table("activities")
    op.drop_table("opportunities")
    op.drop_table("contacts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in [
        "paymentmethod",
        "invoicestatus",
        "salesorderstatus",
        "approvalstatus",
        "quotestatus",
        "activitytype",
        "pipelinestage",
        "opportunitytype",
        "userrole",
    ]:
        enum_type = sa.Enum(name=enum_name)
        enum_type.drop(bind, checkfirst=True)
