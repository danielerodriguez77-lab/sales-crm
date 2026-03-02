import json
import os

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


DEFAULT_USERS = [
    {
        "name": "Gerente de Ventas",
        "email": "manager@example.com",
        "role": "manager",
        "team": None,
        "password": "manager123",
        "active": True,
    },
    {
        "name": "Supervisor de Ventas Agras",
        "email": "supervisor.agras@example.com",
        "role": "supervisor",
        "team": "Agras",
        "password": "supervisor123",
        "active": True,
    },
    {
        "name": "Supervisor de Ventas Enterprise",
        "email": "supervisor.enterprise@example.com",
        "role": "supervisor",
        "team": "Enterprise",
        "password": "supervisor123",
        "active": True,
    },
    {
        "name": "Vendedor Agras 1",
        "email": "seller.agras1@example.com",
        "role": "seller",
        "team": "Agras",
        "password": "seller123",
        "active": True,
    },
    {
        "name": "Vendedor Agras 2",
        "email": "seller.agras2@example.com",
        "role": "seller",
        "team": "Agras",
        "password": "seller123",
        "active": True,
    },
    {
        "name": "Vendedor Enterprise 1",
        "email": "seller.enterprise1@example.com",
        "role": "seller",
        "team": "Enterprise",
        "password": "seller123",
        "active": True,
    },
    {
        "name": "Vendedor Enterprise 2",
        "email": "seller.enterprise2@example.com",
        "role": "seller",
        "team": "Enterprise",
        "password": "seller123",
        "active": True,
    },
]


def _load_users() -> list[dict]:
    raw = os.getenv("CRM_USER_SEED")
    if not raw:
        return DEFAULT_USERS
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CRM_USER_SEED no es JSON válido") from exc
    if not isinstance(data, list):
        raise RuntimeError("CRM_USER_SEED debe ser una lista de usuarios")
    return data


def _role(value: str) -> UserRole:
    try:
        return UserRole(value)
    except ValueError as exc:
        raise RuntimeError(f"Rol inválido: {value}") from exc


def sync_users() -> None:
    users = _load_users()
    db = SessionLocal()
    try:
        manager_email = next(
            (u["email"] for u in users if u.get("role") == "manager"),
            None,
        )
        manager = None
        if manager_email:
            manager = db.query(User).filter(User.email == manager_email).first()

        for entry in users:
            email = entry["email"]
            user = db.query(User).filter(User.email == email).first()
            role = _role(entry.get("role", "seller"))
            password = entry.get("password")
            if user:
                if entry.get("name") is not None:
                    user.name = entry["name"]
                user.role = role
                user.team = entry.get("team")
                if entry.get("active") is not None:
                    user.active = bool(entry.get("active"))
                if password:
                    user.password_hash = hash_password(password)
                if manager:
                    user.updated_by_id = manager.id
            else:
                user = User(
                    name=entry["name"],
                    email=email,
                    role=role,
                    team=entry.get("team"),
                    password_hash=hash_password(password or "change_me"),
                    active=bool(entry.get("active", True)),
                )
                if manager:
                    user.created_by_id = manager.id
                    user.updated_by_id = manager.id
                db.add(user)
                db.flush()
                if manager is None and role == UserRole.manager:
                    manager = user

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    sync_users()
