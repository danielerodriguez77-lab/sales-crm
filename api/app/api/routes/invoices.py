from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.invoice import Invoice
from app.models.opportunity import Opportunity
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.models.enums import PipelineStage
from app.schemas.invoice import InvoiceCreate, InvoiceRead, InvoiceUpdate
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _generate_invoice_number(db: Session) -> str:
    count = db.query(Invoice).count() + 1
    return f"F-{count:06d}"


@router.get("", response_model=list[InvoiceRead])
def invoices_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    opportunity_id: int | None = None,
):
    query = db.query(Invoice)
    if opportunity_id is not None:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        ensure_opportunity_access(current_user, opportunity)
        query = query.join(SalesOrder).filter(SalesOrder.opportunity_id == opportunity_id)
    else:
        if is_manager(current_user):
            pass
        elif is_supervisor(current_user):
            query = (
                query.join(SalesOrder)
                .join(Opportunity)
                .join(User, Opportunity.assigned_to_id == User.id)
            )
            if current_user.team:
                query = query.filter(User.team == current_user.team)
            else:
                query = query.filter(User.id == -1)
        else:
            query = (
                query.join(SalesOrder)
                .join(Opportunity)
                .filter(Opportunity.assigned_to_id == current_user.id)
            )
    return query.order_by(Invoice.id.desc()).all()


@router.post("", response_model=InvoiceRead)
def invoices_create(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(SalesOrder).filter(SalesOrder.id == payload.sales_order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    number = payload.number or _generate_invoice_number(db)

    invoice = Invoice(
        sales_order_id=payload.sales_order_id,
        number=number,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        total=payload.total,
        status=payload.status,
        invoice_type=payload.invoice_type,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    opportunity.stage = PipelineStage.facturacion
    opportunity.updated_by_id = current_user.id
    db.add(invoice)
    db.flush()
    log_action(db, current_user.id, "Invoice", invoice.id, "create", after=snapshot(invoice))
    db.commit()
    db.refresh(invoice)
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def invoices_update(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    before = snapshot(invoice)
    if payload.sales_order_id is not None and payload.sales_order_id != invoice.sales_order_id:
        new_order = db.query(SalesOrder).filter(SalesOrder.id == payload.sales_order_id).first()
        if not new_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
        new_opp = db.query(Opportunity).filter(Opportunity.id == new_order.opportunity_id).first()
        if not new_opp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oportunidad no encontrada")
        ensure_opportunity_access(current_user, new_opp)
        invoice.sales_order_id = payload.sales_order_id
        new_opp.stage = PipelineStage.facturacion
        new_opp.updated_by_id = current_user.id

    for field in ["number", "issue_date", "due_date", "total", "status", "invoice_type"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(invoice, field, value)

    invoice.updated_by_id = current_user.id
    log_action(db, current_user.id, "Invoice", invoice.id, "update", before=before, after=snapshot(invoice))
    db.commit()
    db.refresh(invoice)
    return invoice
