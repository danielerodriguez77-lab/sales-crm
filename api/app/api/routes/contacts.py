from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.contact import Contact
from app.models.opportunity import Opportunity
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.permissions import is_manager, is_supervisor

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _seller_can_access_contact(db: Session, contact_id: int, user_id: int) -> bool:
    return (
        db.query(Opportunity)
        .filter(Opportunity.contact_id == contact_id, Opportunity.assigned_to_id == user_id)
        .count()
        > 0
    )


@router.get("", response_model=list[ContactRead])
def contacts_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Contact)
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
        query = query.distinct()
    else:
        query = (
            query.join(Opportunity)
            .filter(Opportunity.assigned_to_id == current_user.id)
            .distinct()
        )
    return query.order_by(Contact.id.desc()).all()


@router.post("", response_model=ContactRead)
def contacts_create(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = Contact(
        name=payload.name,
        tax_id=payload.tax_id,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        payment_terms=payload.payment_terms,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
def contacts_update(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    if not is_manager(current_user):
        if is_supervisor(current_user):
            if not current_user.team:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
            count = (
                db.query(Opportunity)
                .join(User, Opportunity.assigned_to_id == User.id)
                .filter(Opportunity.contact_id == contact_id, User.team == current_user.team)
                .count()
            )
            if count == 0:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        else:
            if not _seller_can_access_contact(db, contact_id, current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    for field in ["name", "tax_id", "email", "phone", "address", "payment_terms"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(contact, field, value)
    contact.updated_by_id = current_user.id
    db.commit()
    db.refresh(contact)
    return contact
