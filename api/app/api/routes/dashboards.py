from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activity import Activity
from app.models.enums import PipelineStage, QuoteStatus, UserRole
from app.models.invoice import Invoice
from app.models.opportunity import Opportunity
from app.models.payment import Payment
from app.models.quote import Quote
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.services.permissions import is_manager, is_supervisor

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def _opps_query(db: Session, user: User, start: datetime | None, end: datetime | None):
    query = db.query(Opportunity)
    if is_manager(user):
        pass
    elif is_supervisor(user):
        query = query.join(User, Opportunity.assigned_to_id == User.id)
        if user.team:
            query = query.filter(User.team == user.team)
        else:
            query = query.filter(User.id == -1)
    else:
        query = query.filter(Opportunity.assigned_to_id == user.id)
    if start:
        query = query.filter(Opportunity.created_at >= start)
    if end:
        query = query.filter(Opportunity.created_at <= end)
    return query


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
):
    opps_query = _opps_query(db, current_user, start, end)

    pipeline = (
        opps_query.with_entities(Opportunity.stage, func.coalesce(func.sum(Opportunity.estimated_value), 0))
        .group_by(Opportunity.stage)
        .all()
    )
    pipeline_by_stage = {stage.value: float(total or 0) for stage, total in pipeline}

    total_opps = opps_query.count() or 1
    counts_by_stage = (
        opps_query.with_entities(Opportunity.stage, func.count(Opportunity.id))
        .group_by(Opportunity.stage)
        .all()
    )
    conversion_by_stage = {stage.value: round((count / total_opps) * 100, 2) for stage, count in counts_by_stage}

    # avg first response time (hours)
    activity_min = (
        db.query(Activity.opportunity_id, func.min(Activity.activity_at).label("first_activity"))
        .group_by(Activity.opportunity_id)
        .subquery()
    )
    first_response_rows = (
        opps_query.join(activity_min, Opportunity.id == activity_min.c.opportunity_id)
        .with_entities(Opportunity.created_at, activity_min.c.first_activity)
        .all()
    )
    if first_response_rows:
        deltas = [
            (row.first_activity - row.created_at).total_seconds() / 3600
            for row in first_response_rows
        ]
        avg_first_response_hours = round(sum(deltas) / len(deltas), 2)
    else:
        avg_first_response_hours = None

    # avg sales cycle time (days) for won
    won_rows = opps_query.filter(Opportunity.stage.in_([PipelineStage.ganado, PipelineStage.pagado_cerrado]))
    if won_rows.count():
        durations = [
            (row.updated_at - row.created_at).total_seconds() / 86400
            for row in won_rows.all()
        ]
        avg_cycle_days = round(sum(durations) / len(durations), 2)
    else:
        avg_cycle_days = None

    quotes_sent = (
        db.query(Quote)
        .join(Opportunity, Quote.opportunity_id == Opportunity.id)
        .filter(Quote.status == QuoteStatus.sent)
    )
    if is_manager(current_user):
        pass
    elif is_supervisor(current_user):
        quotes_sent = quotes_sent.join(User, Opportunity.assigned_to_id == User.id)
        if current_user.team:
            quotes_sent = quotes_sent.filter(User.team == current_user.team)
        else:
            quotes_sent = quotes_sent.filter(User.id == -1)
    else:
        quotes_sent = quotes_sent.filter(Opportunity.assigned_to_id == current_user.id)
    quotes_sent_count = quotes_sent.count()

    sales_won_count = won_rows.count()

    revenue_by_month = (
        db.query(func.date_trunc("month", SalesOrder.created_at).label("month"), func.sum(SalesOrder.total))
        .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
    )
    if is_manager(current_user):
        pass
    elif is_supervisor(current_user):
        revenue_by_month = revenue_by_month.join(User, Opportunity.assigned_to_id == User.id)
        if current_user.team:
            revenue_by_month = revenue_by_month.filter(User.team == current_user.team)
        else:
            revenue_by_month = revenue_by_month.filter(User.id == -1)
    else:
        revenue_by_month = revenue_by_month.filter(Opportunity.assigned_to_id == current_user.id)
    if start:
        revenue_by_month = revenue_by_month.filter(SalesOrder.created_at >= start)
    if end:
        revenue_by_month = revenue_by_month.filter(SalesOrder.created_at <= end)
    revenue_by_month = revenue_by_month.group_by("month").order_by("month").all()
    revenue_won = [
        {"month": str(row.month.date()), "total": float(row[1] or 0)}
        for row in revenue_by_month
    ]

    collected_by_month = (
        db.query(func.date_trunc("month", Payment.date).label("month"), func.sum(Payment.amount))
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .join(SalesOrder, Invoice.sales_order_id == SalesOrder.id)
        .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
    )
    if is_manager(current_user):
        pass
    elif is_supervisor(current_user):
        collected_by_month = collected_by_month.join(User, Opportunity.assigned_to_id == User.id)
        if current_user.team:
            collected_by_month = collected_by_month.filter(User.team == current_user.team)
        else:
            collected_by_month = collected_by_month.filter(User.id == -1)
    else:
        collected_by_month = collected_by_month.filter(Opportunity.assigned_to_id == current_user.id)
    if start:
        collected_by_month = collected_by_month.filter(Payment.date >= start.date())
    if end:
        collected_by_month = collected_by_month.filter(Payment.date <= end.date())
    collected_by_month = collected_by_month.group_by("month").order_by("month").all()
    collected = [
        {"month": str(row.month.date()), "total": float(row[1] or 0)}
        for row in collected_by_month
    ]

    # ranking sellers
    if is_manager(current_user):
        sellers = db.query(User).all()
    elif is_supervisor(current_user):
        if current_user.team:
            sellers = (
                db.query(User)
                .filter(User.team == current_user.team, User.role == UserRole.seller)
                .all()
            )
        else:
            sellers = []
    else:
        sellers = [current_user]
    ranking = []
    for seller in sellers:
        seller_opps = db.query(Opportunity).filter(Opportunity.assigned_to_id == seller.id)
        total = seller_opps.count() or 1
        won = seller_opps.filter(Opportunity.stage.in_([PipelineStage.ganado, PipelineStage.pagado_cerrado])).count()
        conversion = round((won / total) * 100, 2)
        activity_count = db.query(Activity).filter(Activity.user_id == seller.id).count()
        revenue = (
            db.query(func.coalesce(func.sum(SalesOrder.total), 0))
            .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
            .filter(Opportunity.assigned_to_id == seller.id)
            .scalar()
        )
        order_count = (
            db.query(SalesOrder)
            .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
            .filter(Opportunity.assigned_to_id == seller.id)
            .count()
        )
        avg_ticket = float(revenue or 0) / order_count if order_count else 0
        ranking.append(
            {
                "seller_id": seller.id,
                "seller": seller.name,
                "revenue": float(revenue or 0),
                "conversion": conversion,
                "activity_volume": activity_count,
                "avg_ticket": round(avg_ticket, 2),
            }
        )

    return {
        "pipeline_by_stage": pipeline_by_stage,
        "conversion_by_stage": conversion_by_stage,
        "avg_first_response_hours": avg_first_response_hours,
        "avg_sales_cycle_days": avg_cycle_days,
        "quotes_sent": quotes_sent_count,
        "sales_won": sales_won_count,
        "revenue_won_by_month": revenue_won,
        "collected_by_month": collected,
        "ranking": ranking,
    }
