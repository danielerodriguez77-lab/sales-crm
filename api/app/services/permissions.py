from fastapi import HTTPException, status

from app.models.enums import UserRole
from app.models.opportunity import Opportunity
from app.models.user import User


def is_manager(user: User) -> bool:
    return user.role in {UserRole.manager, UserRole.admin}


def is_supervisor(user: User) -> bool:
    return user.role == UserRole.supervisor


def ensure_opportunity_access(user: User, opportunity: Opportunity) -> None:
    if is_manager(user):
        return
    if is_supervisor(user):
        assigned = opportunity.assigned_user
        if assigned and user.team and assigned.team == user.team:
            return
    if opportunity.assigned_to_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
