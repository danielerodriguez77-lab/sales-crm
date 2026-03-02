from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.invoice import Invoice
from app.models.opportunity import Opportunity
from app.models.payment import Payment
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.models.enums import InvoiceStatus, PipelineStage
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot

router = APIRouter(prefix="/payments", tags=["payments"])


def _recalculate_invoice_status(db: Session, invoice: Invoice) -> None:
    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice.id)
        .scalar()
    )
    if total_paid >= invoice.total:
        invoice.status = InvoiceStatus.paid
    elif total_paid > 0:
        invoice.status = InvoiceStatus.partial
    else:
        if invoice.status == InvoiceStatus.paid:
            invoice.status = InvoiceStatus.issued


@router.get("", response_model=list[PaymentRead])
def payments_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    invoice_id: int | None = None,
):
    query = db.query(Payment)
    if invoice_id is not None:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        order = db.query(SalesOrder).filter(SalesOrder.id == invoice.sales_order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        ensure_opportunity_access(current_user, opportunity)
        query = query.filter(Payment.invoice_id == invoice_id)
    else:
        if is_manager(current_user):
            pass
        elif is_supervisor(current_user):
            query = (
                query.join(Invoice)
                .join(SalesOrder)
                .join(Opportunity)
                .join(User, Opportunity.assigned_to_id == User.id)
            )
            if current_user.team:
                query = query.filter(User.team == current_user.team)
            else:
                query = query.filter(User.id == -1)
        else:
            query = (
                query.join(Invoice)
                .join(SalesOrder)
                .join(Opportunity)
                .filter(Opportunity.assigned_to_id == current_user.id)
            )
    return query.order_by(Payment.date.desc()).all()


@router.post("", response_model=PaymentRead)
def payments_create(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    order = db.query(SalesOrder).filter(SalesOrder.id == invoice.sales_order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    existing_total = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == payload.invoice_id)
        .scalar()
    )
    if existing_total + payload.amount > invoice.total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago excede el total de la factura",
        )

    payment = Payment(
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        date=payload.date,
        method=payload.method,
        reference=payload.reference,
        attachment_path=payload.attachment_path,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(payment)
    db.flush()
    log_action(db, current_user.id, "Payment", payment.id, "create", after=snapshot(payment))
    _recalculate_invoice_status(db, invoice)
    if invoice.status == InvoiceStatus.paid:
        opportunity.stage = PipelineStage.pagado_cerrado
    elif invoice.status == InvoiceStatus.partial:
        opportunity.stage = PipelineStage.cobro_parcial
    opportunity.updated_by_id = current_user.id
    db.commit()
    db.refresh(payment)
    return payment


@router.patch("/{payment_id}", response_model=PaymentRead)
def payments_update(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    order = db.query(SalesOrder).filter(SalesOrder.id == invoice.sales_order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    before = snapshot(payment)
    if payload.amount is not None:
        other_total = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.invoice_id == payment.invoice_id, Payment.id != payment.id)
            .scalar()
        )
        if other_total + payload.amount > invoice.total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El pago excede el total de la factura",
            )

    before = snapshot(payment)
    for field in ["amount", "date", "method", "reference", "attachment_path"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(payment, field, value)

    payment.updated_by_id = current_user.id
    log_action(db, current_user.id, "Payment", payment.id, "update", before=before, after=snapshot(payment))
    _recalculate_invoice_status(db, invoice)
    if invoice.status == InvoiceStatus.paid:
        opportunity.stage = PipelineStage.pagado_cerrado
    elif invoice.status == InvoiceStatus.partial:
        opportunity.stage = PipelineStage.cobro_parcial
    opportunity.updated_by_id = current_user.id
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}")
def payments_delete(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    order = db.query(SalesOrder).filter(SalesOrder.id == invoice.sales_order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    before = snapshot(payment)
    db.delete(payment)
    db.flush()
    _recalculate_invoice_status(db, invoice)
    if invoice.status == InvoiceStatus.paid:
        opportunity.stage = PipelineStage.pagado_cerrado
    elif invoice.status == InvoiceStatus.partial:
        opportunity.stage = PipelineStage.cobro_parcial
    opportunity.updated_by_id = current_user.id
    log_action(db, current_user.id, "Payment", payment.id, "delete", before=before, after=None)
    db.commit()
    return {"status": "deleted"}
