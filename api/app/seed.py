from datetime import datetime, timedelta, timezone, date

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import (
    OpportunityType,
    PipelineStage,
    QuoteStatus,
    InvoiceStatus,
    PaymentMethod,
    UserRole,
    ActivityType,
    SalesOrderStatus,
    InvoiceType,
)
from app.models.user import User
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.payment import Payment


def seed():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        manager = User(
            name="Gerente de Ventas",
            email="manager@example.com",
            role=UserRole.manager,
            password_hash=hash_password("manager123"),
            active=True,
        )
        supervisor_agras = User(
            name="Supervisor de Ventas Agras",
            email="supervisor.agras@example.com",
            role=UserRole.supervisor,
            team="Agras",
            password_hash=hash_password("supervisor123"),
            active=True,
        )
        supervisor_enterprise = User(
            name="Supervisor de Ventas Enterprise",
            email="supervisor.enterprise@example.com",
            role=UserRole.supervisor,
            team="Enterprise",
            password_hash=hash_password("supervisor123"),
            active=True,
        )
        seller1 = User(
            name="Vendedor Agras 1",
            email="seller.agras1@example.com",
            role=UserRole.seller,
            team="Agras",
            password_hash=hash_password("seller123"),
            active=True,
        )
        seller2 = User(
            name="Vendedor Agras 2",
            email="seller.agras2@example.com",
            role=UserRole.seller,
            team="Agras",
            password_hash=hash_password("seller123"),
            active=True,
        )
        seller3 = User(
            name="Vendedor Enterprise 1",
            email="seller.enterprise1@example.com",
            role=UserRole.seller,
            team="Enterprise",
            password_hash=hash_password("seller123"),
            active=True,
        )
        seller4 = User(
            name="Vendedor Enterprise 2",
            email="seller.enterprise2@example.com",
            role=UserRole.seller,
            team="Enterprise",
            password_hash=hash_password("seller123"),
            active=True,
        )
        db.add_all(
            [
                manager,
                supervisor_agras,
                supervisor_enterprise,
                seller1,
                seller2,
                seller3,
                seller4,
            ]
        )
        db.flush()

        lead1 = Opportunity(
            record_type=OpportunityType.lead,
            company_name="Acme Corp",
            stage=PipelineStage.lead_nuevo,
            estimated_value=15000,
            assigned_to_id=seller1.id,
            next_action_at=datetime.now(timezone.utc) + timedelta(days=1),
            created_by_id=manager.id,
            updated_by_id=manager.id,
        )
        lead2 = Opportunity(
            record_type=OpportunityType.opportunity,
            company_name="Globex Enterprise",
            stage=PipelineStage.oferta_enviada,
            estimated_value=28000,
            assigned_to_id=seller3.id,
            next_action_at=datetime.now(timezone.utc) + timedelta(days=2),
            created_by_id=manager.id,
            updated_by_id=manager.id,
        )
        db.add_all([lead1, lead2])
        db.flush()

        activity = Activity(
            opportunity_id=lead2.id,
            user_id=seller3.id,
            activity_type=ActivityType.call,
            activity_at=datetime.now(timezone.utc) - timedelta(days=1),
            notes="Llamada inicial",
            created_by_id=seller3.id,
            updated_by_id=seller3.id,
        )
        db.add(activity)

        quote = Quote(
            opportunity_id=lead2.id,
            number="Q-000001",
            status=QuoteStatus.sent,
            version=1,
            subtotal=25000,
            tax=3000,
            total=28000,
            discount_percent=0,
            created_by_id=seller3.id,
            updated_by_id=seller3.id,
        )
        db.add(quote)
        db.flush()

        order = SalesOrder(
            opportunity_id=lead2.id,
            quote_id=quote.id,
            status=SalesOrderStatus.open,
            subtotal=25000,
            tax=3000,
            total=28000,
            created_by_id=seller3.id,
            updated_by_id=seller3.id,
        )
        db.add(order)
        db.flush()

        invoice = Invoice(
            sales_order_id=order.id,
            number="F-000001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=10),
            total=28000,
            status=InvoiceStatus.issued,
            invoice_type=InvoiceType.total,
            created_by_id=seller3.id,
            updated_by_id=seller3.id,
        )
        db.add(invoice)
        db.flush()

        payment = Payment(
            invoice_id=invoice.id,
            amount=10000,
            date=date.today(),
            method=PaymentMethod.transfer,
            reference="TRX-123",
            created_by_id=seller3.id,
            updated_by_id=seller3.id,
        )
        db.add(payment)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
