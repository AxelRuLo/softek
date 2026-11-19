from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture
def api(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def test_session():
        with Session(engine) as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = test_session
    monkeypatch.setattr("app.main.create_db_and_tables", lambda: None)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        engine.dispose()


def test_functional_sales_workflow(api):
    clients = []
    for name in ("Ada", "Bob", "Cleo"):
        response = api.post(
            "/clients", json={"name": name, "email": f"{name.lower()}@example.com", "password": "secret"}
        )
        assert response.status_code == 201
        assert "password" not in response.json()
        clients.append(response.json())

    assert api.post("/clients", json={"name": "Bad", "email": "invalid", "password": "secret"}).status_code == 422
    assert api.post("/clients", json={"name": "Duplicate", "email": "ada@example.com", "password": "secret"}).status_code == 409

    services = []
    for name in ("Original", "Standard"):
        response = api.post("/services", json={"name": name, "description": f"{name} description", "suggested_price": 100})
        assert response.status_code == 201
        services.append(response.json())
    assert api.post("/services", json={"name": "Invalid", "description": "Bad price", "suggested_price": 0}).status_code == 422
    assert api.post("/services", json={"name": "Standard", "description": "Duplicate", "suggested_price": 100}).status_code == 409

    def create_order(client, service):
        response = api.post("/orders", json={"client_id": client["id"], "service_id": service["id"]})
        assert response.status_code == 201
        return response.json()

    first = create_order(clients[0], services[0])
    response = api.patch(f"/services/{services[0]['id']}", json={"suggested_price": 900, "description": "Changed"})
    assert response.status_code == 200
    assert response.json()["suggested_price"] == 900

    orders = [first]
    for client, count in ((clients[0], 4), (clients[1], 5), (clients[2], 2)):
        orders.extend(create_order(client, services[1]) for _ in range(count))

    assert api.post("/orders", json={"client_id": str(uuid4()), "service_id": services[0]["id"]}).status_code == 404
    assert api.post("/orders", json={"client_id": clients[0]["id"], "service_id": str(uuid4())}).status_code == 404
    assert api.post("/orders", json={"client_id": clients[0]["id"], "service_id": services[0]["id"], "suggested_price": 1}).status_code == 422

    cancelled = create_order(clients[0], services[0])
    deleted = create_order(clients[1], services[0])
    assert api.post(f"/orders/{cancelled['id']}/cancel").status_code == 200
    assert api.delete(f"/orders/{deleted['id']}").status_code == 204
    assert api.delete(f"/clients/{clients[0]['id']}").status_code == 204

    snapshot = api.get(f"/orders/{first['id']}")
    assert snapshot.status_code == 200
    assert snapshot.json()["suggested_price"] == 100
    assert snapshot.json()["service_description"] == "Original description"

    response = api.get("/reports/sales/recent")
    assert response.status_code == 200
    recent = response.json()
    expected_orders = sorted(orders, key=lambda order: (order["created_at"], order["id"]), reverse=True)[:10]
    names = {client["id"]: client["name"] for client in clients}
    assert recent == [
        {"client_name": names[order["client_id"]], "service_description": order["service_description"],
         "suggested_price": order["suggested_price"], "created_at": order["created_at"]}
        for order in expected_orders
    ]
    assert len(recent) == 10

    expected = sorted(
        [{"client_id": client["id"], "client_name": client["name"], "order_count": count, "total_cents": count * 100}
         for client, count in zip(clients, (5, 5, 2))],
        key=lambda item: (-item["total_cents"], item["client_id"]),
    )
    response = api.get("/reports/sales/by-client")
    assert response.status_code == 200
    assert response.json() == expected
    page = api.get("/reports/sales/by-client", params={"offset": 1, "limit": 1})
    assert page.status_code == 200
    assert page.json() == expected[1:2]
    assert api.get("/reports/sales/by-client", params={"offset": 3, "limit": 1}).json() == []
    assert api.get("/reports/sales/by-client", params={"offset": -1}).status_code == 422
    assert api.get("/reports/sales/by-client", params={"limit": 101}).status_code == 422
