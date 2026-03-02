from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskRead, TaskUpdate
from app.services.permissions import is_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def tasks_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task)
    if not is_manager(current_user):
        query = query.filter(Task.user_id == current_user.id)
    return query.order_by(Task.due_at.asc().nullslast()).all()


@router.patch("/{task_id}", response_model=TaskRead)
def tasks_update(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    if not is_manager(current_user) and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    for field in ["status", "due_at", "description"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(task, field, value)

    task.updated_by_id = current_user.id
    db.commit()
    db.refresh(task)
    return task
