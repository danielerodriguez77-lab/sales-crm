from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.enums import OpportunityType, PipelineStage, UserRole
from app.models.opportunity import Opportunity
from app.models.user import User


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_seller_cannot_access_other_opportunity(client, db_session):
    seller1 = User(
        name="Seller1",
        email="s1@test.com",
        role=UserRole.seller,
        password_hash=hash_password("pass"),
        active=True,
    )
    seller2 = User(
        name="Seller2",
        email="s2@test.com",
        role=UserRole.seller,
        password_hash=hash_password("pass"),
        active=True,
    )
    db_session.add_all([seller1, seller2])
    db_session.commit()

    opp = Opportunity(
        record_type=OpportunityType.lead,
        company_name="Other",
        stage=PipelineStage.lead_nuevo,
        assigned_to_id=seller2.id,
        no_next_action=True,
    )
    db_session.add(opp)
    db_session.commit()

    token = _login(client, "s1@test.com", "pass")
    res = client.get(f"/api/opportunities/{opp.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_stage_requires_quote(client, db_session):
    seller = User(
        name="Seller",
        email="s3@test.com",
        role=UserRole.seller,
        password_hash=hash_password("pass"),
        active=True,
    )
    db_session.add(seller)
    db_session.commit()

    opp = Opportunity(
        record_type=OpportunityType.opportunity,
        company_name="Stage Test",
        stage=PipelineStage.calificado,
        assigned_to_id=seller.id,
        no_next_action=True,
    )
    db_session.add(opp)
    db_session.commit()

    token = _login(client, "s3@test.com", "pass")
    res = client.patch(
        f"/api/opportunities/{opp.id}",
        json={"stage": "oferta_enviada"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
