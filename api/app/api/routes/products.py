from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.permissions import is_manager

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def products_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post("", response_model=ProductRead)
def products_create(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    product = Product(
        name=payload.name,
        sku=payload.sku,
        price=payload.price,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductRead)
def products_update(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_manager(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    for field in ["name", "sku", "price"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(product, field, value)
    product.updated_by_id = current_user.id
    db.commit()
    db.refresh(product)
    return product
