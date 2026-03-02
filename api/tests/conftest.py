import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["APP_ENV"] = "test"

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def manager_user(db_session):
    user = User(
        name="Manager",
        email="manager@test.com",
        role=UserRole.manager,
        password_hash=hash_password("pass"),
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def seller_user(db_session):
    user = User(
        name="Seller",
        email="seller@test.com",
        role=UserRole.seller,
        password_hash=hash_password("pass"),
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
