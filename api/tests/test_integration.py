from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_full_sales_flow(client, db_session):
    seller = User(
        name="Seller",
        email="seller@flow.com",
        role=UserRole.seller,
        password_hash=hash_password("pass"),
        active=True,
    )
    db_session.add(seller)
    db_session.commit()

    token = _login(client, "seller@flow.com", "pass")

    # create opportunity
    res = client.post(
        "/api/opportunities",
        json={
            "record_type": "lead",
            "company_name": "Flow Co",
            "estimated_value": 1000,
            "next_action_at": "2030-01-01T10:00:00Z",
            "no_next_action": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    opp_id = res.json()["id"]

    # create activity
    res = client.post(
        "/api/activities",
        json={
            "opportunity_id": opp_id,
            "activity_type": "call",
            "activity_at": "2030-01-01T11:00:00Z",
            "notes": "Call",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    # create quote
    res = client.post(
        "/api/quotes",
        json={
            "opportunity_id": opp_id,
            "items": [{"name": "Servicio", "quantity": 1, "price": 1000, "subtotal": 1000}],
            "subtotal": 1000,
            "tax": 0,
            "total": 1000,
            "discount_percent": 0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    quote_id = res.json()["id"]

    # send quote
    res = client.post(
        f"/api/quotes/{quote_id}/send",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    # create sales order
    res = client.post(
        "/api/sales-orders",
        json={
            "opportunity_id": opp_id,
            "quote_id": quote_id,
            "subtotal": 1000,
            "tax": 0,
            "total": 1000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    order_id = res.json()["id"]

    # create invoice
    res = client.post(
        "/api/invoices",
        json={
            "sales_order_id": order_id,
            "issue_date": "2030-01-01",
            "due_date": "2030-01-10",
            "total": 1000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    invoice_id = res.json()["id"]

    # create payment
    res = client.post(
        "/api/payments",
        json={
            "invoice_id": invoice_id,
            "amount": 1000,
            "date": "2030-01-05",
            "method": "transfer",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
