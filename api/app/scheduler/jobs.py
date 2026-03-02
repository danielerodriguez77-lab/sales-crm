from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.alert import Alert
from app.models.enums import (
    AlertScope,
    AlertType,
    OpportunityType,
    PipelineStage,
    TaskStatus,
    TaskType,
    InvoiceStatus,
)
from app.models.invoice import Invoice
from app.models.opportunity import Opportunity
from app.models.sales_order import SalesOrder
from app.models.task import Task


def _create_task(db, user_id: int, opportunity_id: int | None, task_type: TaskType, title: str, due_at=None):
    exists = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.opportunity_id == opportunity_id,
            Task.task_type == task_type,
            Task.status == TaskStatus.open,
        )
        .first()
    )
    if exists:
        return
    task = Task(
        title=title,
        description=None,
        due_at=due_at,
        status=TaskStatus.open,
        task_type=task_type,
        user_id=user_id,
        opportunity_id=opportunity_id,
    )
    db.add(task)


def _create_alert(db, scope: AlertScope, alert_type: AlertType, message: str, opportunity_id=None, user_id=None):
    exists = (
        db.query(Alert)
        .filter(
            Alert.scope == scope,
            Alert.alert_type == alert_type,
            Alert.opportunity_id == opportunity_id,
            Alert.resolved_at.is_(None),
        )
        .first()
    )
    if exists:
        return
    alert = Alert(
        scope=scope,
        alert_type=alert_type,
        message=message,
        opportunity_id=opportunity_id,
        user_id=user_id,
    )
    db.add(alert)


def sla_first_contact_check():
    db = SessionLocal()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(hours=settings.sla_first_contact_hours)
        activity_subq = db.query(Activity.opportunity_id).distinct().subquery()
        leads = (
            db.query(Opportunity)
            .filter(Opportunity.record_type == OpportunityType.lead)
            .filter(Opportunity.created_at <= threshold)
            .filter(~Opportunity.id.in_(activity_subq))
            .all()
        )
        for lead in leads:
            if not lead.assigned_to_id:
                continue
            _create_task(
                db,
                user_id=lead.assigned_to_id,
                opportunity_id=lead.id,
                task_type=TaskType.sla_first_contact,
                title="Contactar lead nuevo (SLA)",
                due_at=datetime.now(timezone.utc),
            )
            _create_alert(
                db,
                scope=AlertScope.manager,
                alert_type=AlertType.sla_first_contact,
                message=f"Lead {lead.id} sin contacto en SLA",
                opportunity_id=lead.id,
            )
        db.commit()
    finally:
        db.close()


def stale_opportunity_check():
    db = SessionLocal()
    try:
        threshold = datetime.now(timezone.utc) - timedelta(days=settings.stale_opportunity_days)
        stages = [
            PipelineStage.calificado,
            PipelineStage.contacto_seguimiento,
            PipelineStage.oferta_enviada,
            PipelineStage.negociacion,
        ]
        last_activity = (
            db.query(Activity.opportunity_id, func.max(Activity.activity_at).label("last_activity"))
            .group_by(Activity.opportunity_id)
            .subquery()
        )
        opportunities = (
            db.query(Opportunity)
            .outerjoin(last_activity, Opportunity.id == last_activity.c.opportunity_id)
            .filter(Opportunity.stage.in_(stages))
            .filter(
                (last_activity.c.last_activity.is_(None))
                | (last_activity.c.last_activity <= threshold)
            )
            .all()
        )
        for opp in opportunities:
            if not opp.assigned_to_id:
                continue
            _create_task(
                db,
                user_id=opp.assigned_to_id,
                opportunity_id=opp.id,
                task_type=TaskType.stale_opportunity,
                title="Oportunidad estancada: requiere seguimiento",
                due_at=datetime.now(timezone.utc),
            )
            _create_alert(
                db,
                scope=AlertScope.manager,
                alert_type=AlertType.stale_opportunity,
                message=f"Oportunidad {opp.id} estancada sin actividad",
                opportunity_id=opp.id,
            )
        db.commit()
    finally:
        db.close()


def payment_reminder_check():
    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).date()
        upcoming = today + timedelta(days=settings.payment_reminder_days_before)
        invoices = (
            db.query(Invoice)
            .filter(Invoice.status.in_([InvoiceStatus.issued, InvoiceStatus.partial, InvoiceStatus.overdue]))
            .all()
        )
        for inv in invoices:
            order = db.query(SalesOrder).filter(SalesOrder.id == inv.sales_order_id).first()
            if not order or not order.opportunity or not order.opportunity.assigned_to_id:
                continue
            opp_id = order.opportunity_id
            seller_id = order.opportunity.assigned_to_id
            if inv.due_date == upcoming:
                _create_task(
                    db,
                    user_id=seller_id,
                    opportunity_id=opp_id,
                    task_type=TaskType.payment_due,
                    title=f"Recordatorio de pago: factura {inv.number}",
                    due_at=datetime.now(timezone.utc),
                )
                _create_alert(
                    db,
                    scope=AlertScope.manager,
                    alert_type=AlertType.payment_due,
                    message=f"Factura {inv.number} vence en {settings.payment_reminder_days_before} días",
                    opportunity_id=opp_id,
                )
            if inv.due_date < today and inv.status != InvoiceStatus.paid:
                inv.status = InvoiceStatus.overdue
                _create_task(
                    db,
                    user_id=seller_id,
                    opportunity_id=opp_id,
                    task_type=TaskType.payment_overdue,
                    title=f"Pago vencido: factura {inv.number}",
                    due_at=datetime.now(timezone.utc),
                )
                _create_alert(
                    db,
                    scope=AlertScope.manager,
                    alert_type=AlertType.payment_overdue,
                    message=f"Factura {inv.number} vencida",
                    opportunity_id=opp_id,
                )
        db.commit()
    finally:
        db.close()
