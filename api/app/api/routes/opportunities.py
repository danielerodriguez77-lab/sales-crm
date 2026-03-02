from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import PipelineStage, QuoteStatus
from app.models.opportunity import Opportunity
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.opportunity import OpportunityCreate, OpportunityRead, OpportunityUpdate
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _ensure_next_action(next_action_at: datetime | None, no_next_action: bool | None):
    if no_next_action:
        return None
    if not next_action_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe definir próxima acción o marcar sin próxima acción",
        )
    return next_action_at


def _ensure_stage_rules(
    db: Session,
    opportunity: Opportunity,
    new_stage: PipelineStage,
    allow_unpaid_close: bool,
    user: User,
):
    if new_stage == PipelineStage.oferta_enviada:
        quote_count = (
            db.query(Quote).filter(Quote.opportunity_id == opportunity.id).count()
        )
        if quote_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede pasar a Oferta Enviada sin cotización",
            )

    if new_stage == PipelineStage.ganado:
        sent_quotes = (
            db.query(Quote)
            .filter(
                Quote.opportunity_id == opportunity.id,
                Quote.status.in_([QuoteStatus.sent, QuoteStatus.accepted]),
            )
            .count()
        )
        if sent_quotes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede pasar a Ganado sin cotización enviada/aprobada",
            )

    if new_stage == PipelineStage.pagado_cerrado:
        invoices = (
            db.query(Invoice)
            .join(SalesOrder, Invoice.sales_order_id == SalesOrder.id)
            .filter(SalesOrder.opportunity_id == opportunity.id)
            .all()
        )
        if not invoices:
            if not (allow_unpaid_close and is_manager(user)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No puede cerrar sin factura pagada",
                )
        else:
            all_paid = all(inv.status.value == "paid" for inv in invoices)
            if not all_paid and not (allow_unpaid_close and is_manager(user)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No puede cerrar sin cobro total",
                )


@router.get("", response_model=list[OpportunityRead])
def opportunities_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    stage: PipelineStage | None = None,
    assigned_to_id: int | None = None,
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
):
    query = db.query(Opportunity)
    if is_manager(current_user):
        if assigned_to_id is not None:
            query = query.filter(Opportunity.assigned_to_id == assigned_to_id)
    elif is_supervisor(current_user):
        query = query.join(User, Opportunity.assigned_to_id == User.id)
        if current_user.team:
            query = query.filter(User.team == current_user.team)
        else:
            query = query.filter(User.id == -1)
        if assigned_to_id is not None:
            query = query.filter(Opportunity.assigned_to_id == assigned_to_id)
    else:
        query = query.filter(Opportunity.assigned_to_id == current_user.id)

    if stage:
        query = query.filter(Opportunity.stage == stage)
    if created_from:
        query = query.filter(Opportunity.created_at >= created_from)
    if created_to:
        query = query.filter(Opportunity.created_at <= created_to)

    return query.order_by(Opportunity.id.desc()).all()


@router.post("", response_model=OpportunityRead)
def opportunities_create(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    next_action = _ensure_next_action(payload.next_action_at, payload.no_next_action)
    assigned_to_id = payload.assigned_to_id
    if not is_manager(current_user):
        assigned_to_id = current_user.id

    opportunity = Opportunity(
        record_type=payload.record_type,
        company_name=payload.company_name,
        person_name=payload.person_name,
        email=payload.email,
        phone=payload.phone,
        source=payload.source,
        segment=payload.segment,
        estimated_value=payload.estimated_value,
        probability=payload.probability,
        stage=payload.stage,
        assigned_to_id=assigned_to_id,
        contact_id=payload.contact_id,
        next_action_at=next_action,
        no_next_action=payload.no_next_action,
        notes=payload.notes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(opportunity)
    db.flush()
    log_action(db, current_user.id, "Opportunity", opportunity.id, "create", after=snapshot(opportunity))
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def opportunities_get(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)
    return opportunity


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
def opportunities_update(
    opportunity_id: int,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    allow_unpaid_close = bool(payload.allow_unpaid_close)

    before = snapshot(opportunity)
    if payload.stage and payload.stage != opportunity.stage:
        _ensure_stage_rules(db, opportunity, payload.stage, allow_unpaid_close, current_user)
        opportunity.stage = payload.stage

    if payload.assigned_to_id is not None:
        if not is_manager(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        opportunity.assigned_to_id = payload.assigned_to_id

    if payload.next_action_at is not None or payload.no_next_action is not None:
        next_action = _ensure_next_action(payload.next_action_at, payload.no_next_action)
        opportunity.next_action_at = next_action
        opportunity.no_next_action = bool(payload.no_next_action)

    for field in [
        "company_name",
        "person_name",
        "email",
        "phone",
        "source",
        "segment",
        "estimated_value",
        "probability",
        "contact_id",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(opportunity, field, value)

    opportunity.updated_by_id = current_user.id
    log_action(db, current_user.id, "Opportunity", opportunity.id, "update", before=before, after=snapshot(opportunity))
    db.commit()
    db.refresh(opportunity)
    return opportunity
