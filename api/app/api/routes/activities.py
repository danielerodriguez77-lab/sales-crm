from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activity import Activity
from app.models.opportunity import Opportunity
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services.permissions import ensure_opportunity_access, is_manager, is_supervisor
from app.services.audit import log_action, snapshot

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityRead])
def activities_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    opportunity_id: int | None = None,
    assigned_to_id: int | None = None,
    stage: str | None = None,
):
    query = db.query(Activity)
    if opportunity_id is not None:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
        ensure_opportunity_access(current_user, opportunity)
        query = query.filter(Activity.opportunity_id == opportunity_id)
    else:
        if is_manager(current_user):
            if assigned_to_id is not None or stage is not None:
                query = query.join(Opportunity)
                if assigned_to_id is not None:
                    query = query.filter(Opportunity.assigned_to_id == assigned_to_id)
                if stage is not None:
                    query = query.filter(Opportunity.stage == stage)
        elif is_supervisor(current_user):
            query = query.join(Opportunity).join(User, Opportunity.assigned_to_id == User.id)
            if current_user.team:
                query = query.filter(User.team == current_user.team)
            else:
                query = query.filter(User.id == -1)
            if assigned_to_id is not None:
                query = query.filter(Opportunity.assigned_to_id == assigned_to_id)
            if stage is not None:
                query = query.filter(Opportunity.stage == stage)
        else:
            query = query.join(Opportunity).filter(Opportunity.assigned_to_id == current_user.id)
    return query.order_by(Activity.activity_at.desc()).all()


@router.post("", response_model=ActivityRead)
def activities_create(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    activity = Activity(
        opportunity_id=payload.opportunity_id,
        user_id=current_user.id,
        activity_type=payload.activity_type,
        activity_at=payload.activity_at,
        outcome=payload.outcome,
        notes=payload.notes,
        next_action_at=payload.next_action_at,
        attachments=payload.attachments,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(activity)
    db.flush()
    log_action(db, current_user.id, "Activity", activity.id, "create", after=snapshot(activity))
    if payload.next_action_at:
        opportunity.next_action_at = payload.next_action_at
        opportunity.no_next_action = False
        opportunity.updated_by_id = current_user.id
    db.commit()
    db.refresh(activity)
    return activity


@router.patch("/{activity_id}", response_model=ActivityRead)
def activities_update(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    opportunity = db.query(Opportunity).filter(Opportunity.id == activity.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    ensure_opportunity_access(current_user, opportunity)

    before = snapshot(activity)
    for field in ["activity_type", "activity_at", "outcome", "notes", "next_action_at", "attachments"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(activity, field, value)

    activity.updated_by_id = current_user.id
    if payload.next_action_at:
        opportunity.next_action_at = payload.next_action_at
        opportunity.no_next_action = False
        opportunity.updated_by_id = current_user.id
    log_action(db, current_user.id, "Activity", activity.id, "update", before=before, after=snapshot(activity))
    db.commit()
    db.refresh(activity)
    return activity
