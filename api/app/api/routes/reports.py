import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import InvoiceStatus, PipelineStage
from app.models.invoice import Invoice
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.models.sales_order import SalesOrder
from app.models.user import User
from app.services.permissions import is_manager

router = APIRouter(prefix="/reports", tags=["reports"])


def _csv_response(filename: str, rows: list[list]):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/seller-performance")
def seller_performance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    rows = [
        [
            "seller_id",
            "seller",
            "revenue",
            "conversion",
            "activity_volume",
            "avg_ticket",
            "contacts_per_week",
        ]
    ]
    sellers = db.query(User).all()
    for seller in sellers:
        seller_opps = db.query(Opportunity).filter(Opportunity.assigned_to_id == seller.id)
        if start:
            seller_opps = seller_opps.filter(Opportunity.created_at >= start)
        if end:
            seller_opps = seller_opps.filter(Opportunity.created_at <= end)
        total = seller_opps.count() or 1
        won = seller_opps.filter(Opportunity.stage.in_([PipelineStage.ganado, PipelineStage.pagado_cerrado])).count()
        conversion = round((won / total) * 100, 2)

        revenue_q = (
            db.query(func.coalesce(func.sum(SalesOrder.total), 0))
            .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
            .filter(Opportunity.assigned_to_id == seller.id)
        )
        if start:
            revenue_q = revenue_q.filter(SalesOrder.created_at >= start)
        if end:
            revenue_q = revenue_q.filter(SalesOrder.created_at <= end)
        revenue = revenue_q.scalar() or 0

        order_count = (
            db.query(SalesOrder)
            .join(Opportunity, SalesOrder.opportunity_id == Opportunity.id)
            .filter(Opportunity.assigned_to_id == seller.id)
            .count()
        )
        avg_ticket = float(revenue) / order_count if order_count else 0
        activity_count = db.query(Activity).filter(Activity.user_id == seller.id).count()

        contacts_query = db.query(Activity).filter(Activity.user_id == seller.id)
        if start:
            contacts_query = contacts_query.filter(Activity.activity_at >= start)
        if end:
            contacts_query = contacts_query.filter(Activity.activity_at <= end)
        contacts_count = contacts_query.count()
        if start or end:
            range_start = start or contacts_query.order_by(Activity.activity_at.asc()).with_entities(Activity.activity_at).first()
            range_end = end or contacts_query.order_by(Activity.activity_at.desc()).with_entities(Activity.activity_at).first()
            if range_start and range_end:
                start_dt = range_start if isinstance(range_start, datetime) else range_start[0]
                end_dt = range_end if isinstance(range_end, datetime) else range_end[0]
                days = max((end_dt - start_dt).days, 0)
                weeks = max((days // 7) + 1, 1)
            else:
                weeks = 1
        else:
            first = contacts_query.order_by(Activity.activity_at.asc()).with_entities(Activity.activity_at).first()
            last = contacts_query.order_by(Activity.activity_at.desc()).with_entities(Activity.activity_at).first()
            if first and last:
                days = max((last[0] - first[0]).days, 0)
                weeks = max((days // 7) + 1, 1)
            else:
                weeks = 1
        contacts_per_week = round(contacts_count / weeks, 2) if weeks else 0

        rows.append(
            [
                seller.id,
                seller.name,
                float(revenue),
                conversion,
                activity_count,
                round(avg_ticket, 2),
                contacts_per_week,
            ]
        )

    return _csv_response("seller_performance.csv", rows)


@router.get("/pipeline-snapshot")
def pipeline_snapshot_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    rows = [["stage", "count", "total_value"]]
    data = (
        db.query(Opportunity.stage, func.count(Opportunity.id), func.coalesce(func.sum(Opportunity.estimated_value), 0))
        .group_by(Opportunity.stage)
        .all()
    )
    for stage, count, total in data:
        rows.append([stage.value, count, float(total)])
    return _csv_response("pipeline_snapshot.csv", rows)


@router.get("/aging")
def aging_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    today = date.today()
    buckets = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    invoices = db.query(Invoice).filter(Invoice.status.in_([InvoiceStatus.issued, InvoiceStatus.partial, InvoiceStatus.overdue])).all()
    for inv in invoices:
        days = (today - inv.due_date).days
        if days <= 30:
            buckets["0-30"] += float(inv.total)
        elif days <= 60:
            buckets["31-60"] += float(inv.total)
        elif days <= 90:
            buckets["61-90"] += float(inv.total)
        else:
            buckets["90+"] += float(inv.total)

    rows = [["bucket", "total"]] + [[k, v] for k, v in buckets.items()]
    return _csv_response("aging_report.csv", rows)
