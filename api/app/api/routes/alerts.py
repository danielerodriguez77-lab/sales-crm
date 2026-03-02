from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.alert import Alert
from app.models.enums import AlertScope
from app.models.user import User
from app.schemas.alert import AlertRead
from app.services.permissions import is_manager

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def alerts_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Alert)
    if is_manager(current_user):
        query = query.filter(Alert.scope.in_([AlertScope.manager, AlertScope.all]))
    else:
        query = query.filter(
            (Alert.scope.in_([AlertScope.seller, AlertScope.all]))
            & (Alert.user_id.is_(None) | (Alert.user_id == current_user.id))
        )
    return query.order_by(Alert.created_at.desc()).all()
