from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import ApprovalStatus, QuoteStatus, PipelineStage
from app.models.opportunity import Opportunity
from app.models.quote import Quote
from app.models.user import User
from app.schemas.quote import QuoteCreate, QuoteRead, QuoteUpdate
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot
from app.services.pdf import generate_quote_pdf

router = APIRouter(prefix="/quotes", tags=["quotes"])


def _generate_quote_number(db: Session) -> str:
    count = db.query(Quote).count() + 1
    return f"Q-{count:06d}"


@router.get("", response_model=list[QuoteRead])
def quotes_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    opportunity_id: int | None = None,
):
    query = db.query(Quote)
    if opportunity_id is not None:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        ensure_opportunity_access(current_user, opportunity)
        query = query.filter(Quote.opportunity_id == opportunity_id)
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
    return query.order_by(Quote.id.desc()).all()


@router.post("", response_model=QuoteRead)
def quotes_create(
    payload: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    latest_version = (
        db.query(Quote)
        .filter(Quote.opportunity_id == payload.opportunity_id)
        .order_by(Quote.version.desc())
        .first()
    )
    version = (latest_version.version + 1) if latest_version else 1
    number = payload.number or _generate_quote_number(db)

    approval_status = ApprovalStatus.not_required
    if payload.discount_percent and payload.discount_percent > settings.discount_threshold_percent:
        approval_status = ApprovalStatus.pending

    quote = Quote(
        opportunity_id=payload.opportunity_id,
        number=number,
        status=QuoteStatus.draft,
        version=version,
        valid_until=payload.valid_until,
        items=payload.items,
        subtotal=payload.subtotal,
        tax=payload.tax,
        total=payload.total,
        discount_percent=payload.discount_percent,
        approval_status=approval_status,
        pdf_path=payload.pdf_path,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(quote)
    db.flush()
    log_action(db, current_user.id, "Quote", quote.id, "create", after=snapshot(quote))
    db.commit()
    db.refresh(quote)
    return quote


@router.patch("/{quote_id}", response_model=QuoteRead)
def quotes_update(
    quote_id: int,
    payload: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    before = snapshot(quote)
    if payload.status == QuoteStatus.sent:
        discount = (
            payload.discount_percent
            if payload.discount_percent is not None
            else quote.discount_percent
        )
        approval = (
            payload.approval_status if payload.approval_status is not None else quote.approval_status
        )
        if discount and discount > settings.discount_threshold_percent and approval != ApprovalStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requiere aprobación de gerente para enviar",
            )
    for field in [
        "status",
        "valid_until",
        "items",
        "subtotal",
        "tax",
        "total",
        "discount_percent",
        "approval_status",
        "pdf_path",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(quote, field, value)

    if (
        payload.discount_percent is not None
        and payload.discount_percent > settings.discount_threshold_percent
        and quote.approval_status != ApprovalStatus.approved
    ):
        quote.approval_status = ApprovalStatus.pending

    quote.updated_by_id = current_user.id
    log_action(db, current_user.id, "Quote", quote.id, "update", before=before, after=snapshot(quote))
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/send", response_model=QuoteRead)
def quotes_send(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    if quote.discount_percent and quote.discount_percent > settings.discount_threshold_percent:
        if quote.approval_status != ApprovalStatus.approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requiere aprobación de gerente para enviar",
            )

    before = snapshot(quote)
    quote.status = QuoteStatus.sent
    quote.sent_at = datetime.now(timezone.utc)
    quote.updated_by_id = current_user.id
    if opportunity.stage != PipelineStage.oferta_enviada:
        opportunity.stage = PipelineStage.oferta_enviada
        opportunity.updated_by_id = current_user.id
    log_action(db, current_user.id, "Quote", quote.id, "send", before=before, after=snapshot(quote))
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/pdf", response_model=QuoteRead)
def quotes_pdf(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    customer_name = "Cliente"
    if opportunity.contact:
        customer_name = opportunity.contact.name
    elif opportunity.company_name:
        customer_name = opportunity.company_name
    elif opportunity.person_name:
        customer_name = opportunity.person_name

    items = quote.items or []
    pdf_path = generate_quote_pdf(quote, customer_name, items)
    before = snapshot(quote)
    quote.pdf_path = pdf_path
    quote.updated_by_id = current_user.id
    log_action(db, current_user.id, "Quote", quote.id, "pdf", before=before, after=snapshot(quote))
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/approve", response_model=QuoteRead)
def quotes_approve(
    quote_id: int,
    approved: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")

    before = snapshot(quote)
    quote.approval_status = ApprovalStatus.approved if approved else ApprovalStatus.rejected
    quote.updated_by_id = current_user.id
    log_action(db, current_user.id, "Quote", quote.id, "approve", before=before, after=snapshot(quote))
    db.commit()
    db.refresh(quote)
    return quote
