from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.security import hash_password
from app.crud.user import create_user, get_user, get_user_by_email, list_users
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit import log_action, snapshot


def _team_scope_users(db: Session, current_user: User):
    if not current_user.team:
        return []
    return (
        db.query(User)
        .filter(User.team == current_user.team)
        .order_by(User.id.asc())
        .all()
    )

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def users_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.manager:
        return list_users(db)
    if current_user.role == UserRole.supervisor:
        return _team_scope_users(db, current_user)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")


@router.post("", response_model=UserRead)
def users_create(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.manager)),
):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        password_hash=hash_password(payload.password),
        active=True,
        team=payload.team,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    created = create_user(db, user)
    log_action(db, current_user.id, "User", created.id, "create", after=snapshot(created))
    db.commit()
    return created


@router.get("/{user_id}", response_model=UserRead)
def users_get(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role == UserRole.manager:
        return user
    if current_user.role == UserRole.supervisor:
        if current_user.team and user.team == current_user.team:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def users_update(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.manager)),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    before = snapshot(user)
    if payload.email and payload.email != user.email:
        if get_user_by_email(db, payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user.email = payload.email
    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role
    if payload.active is not None:
        user.active = payload.active
    if payload.team is not None:
        user.team = payload.team
    if payload.password:
        user.password_hash = hash_password(payload.password)
    user.updated_by_id = current_user.id
    log_action(db, current_user.id, "User", user.id, "update", before=before, after=snapshot(user))
    db.commit()
    db.refresh(user)
    return user
