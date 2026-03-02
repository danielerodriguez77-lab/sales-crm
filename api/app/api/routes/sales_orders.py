from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import QuoteStatus, PipelineStage, SalesOrderStatus
from app.models.opportunity import Opportunity
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.schemas.sales_order import (
    SalesOrderCreate,
    SalesOrderRead,
    SalesOrderUpdate,
    SalesOrderFromOpportunity,
)
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot

router = APIRouter(prefix="/sales-orders", tags=["sales-orders"])


@router.get("", response_model=list[SalesOrderRead])
def sales_orders_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    opportunity_id: int | None = None,
):
    query = db.query(SalesOrder)
    if opportunity_id is not None:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        ensure_opportunity_access(current_user, opportunity)
        query = query.filter(SalesOrder.opportunity_id == opportunity_id)
    else:
        if is_manager(current_user):
            pass
        elif is_supervisor(current_user):
            query = (
                query.join(Opportunity)
                .join(User, Opportunity.assigned_to_id == User.id)
            )
            if current_user.team:
                query = query.filter(User.team == current_user.team)
            else:
                query = query.filter(User.id == -1)
        else:
            query = (
                query.join(Opportunity)
                .filter(Opportunity.assigned_to_id == current_user.id)
            )
    return query.order_by(SalesOrder.id.desc()).all()


@router.post("", response_model=SalesOrderRead)
def sales_orders_create(
    payload: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    quote = db.query(Quote).filter(Quote.id == payload.quote_id).first()
    if not quote or quote.opportunity_id != payload.opportunity_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cotización inválida")
    if quote.status not in [QuoteStatus.sent, QuoteStatus.accepted]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cotización no enviada")

    order = SalesOrder(
        opportunity_id=payload.opportunity_id,
        quote_id=payload.quote_id,
        status=payload.status,
        subtotal=payload.subtotal or quote.subtotal,
        tax=payload.tax or quote.tax,
        total=payload.total or quote.total,
        reference=payload.reference,
        order_date=quote.created_at,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    opportunity.stage = PipelineStage.ganado
    opportunity.updated_by_id = current_user.id
    db.add(order)
    db.flush()
    log_action(db, current_user.id, "SalesOrder", order.id, "create", after=snapshot(order))
    db.commit()
    db.refresh(order)
    return order


@router.post("/from-opportunity", response_model=SalesOrderRead)
def sales_orders_from_opportunity(
    payload: SalesOrderFromOpportunity,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    existing = (
        db.query(SalesOrder)
        .filter(SalesOrder.opportunity_id == payload.opportunity_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Orden ya existe")

    quote_query = db.query(Quote).filter(Quote.opportunity_id == payload.opportunity_id)
    if payload.quote_id is not None:
        quote_query = quote_query.filter(Quote.id == payload.quote_id)
    quote = (
        quote_query.filter(Quote.status.in_([QuoteStatus.sent, QuoteStatus.accepted]))
        .order_by(Quote.created_at.desc())
        .first()
    )
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay cotización enviada/aprobada para crear orden",
        )

    order = SalesOrder(
        opportunity_id=payload.opportunity_id,
        quote_id=quote.id,
        status=SalesOrderStatus.open,
        subtotal=quote.subtotal,
        tax=quote.tax,
        total=quote.total,
        order_date=quote.created_at,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    opportunity.stage = PipelineStage.ganado
    opportunity.updated_by_id = current_user.id
    db.add(order)
    db.flush()
    log_action(db, current_user.id, "SalesOrder", order.id, "create", after=snapshot(order))
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}", response_model=SalesOrderRead)
def sales_orders_update(
    order_id: int,
    payload: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == order.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    before = snapshot(order)
    for field in ["status", "subtotal", "tax", "total", "reference"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(order, field, value)

    order.updated_by_id = current_user.id
    log_action(db, current_user.id, "SalesOrder", order.id, "update", before=before, after=snapshot(order))
    db.commit()
    db.refresh(order)
    return order
