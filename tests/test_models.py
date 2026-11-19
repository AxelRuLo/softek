from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session

from app.client import Client
from app.orders import Order
from app.service import Service
from app.timestamps import utc_now


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as db_session:
            yield db_session
    finally:
        engine.dispose()


def test_entities_generate_uuids_and_new_orders_start_active(session: Session) -> None:
    service = Service(name="Cleaning", description="One hour", suggested_price=1500)
    client = Client(name="Sam", email="sam@example.com", password_hash="hashed")
    session.add_all([service, client])
    session.flush()

    order = Order(
        client_id=client.id,
        service_id=service.id,
        service_name=service.name,
        service_description=service.description,
        suggested_price=service.suggested_price,
    )
    session.add(order)
    session.flush()

    assert all(isinstance(entity.id, UUID) for entity in (service, client, order))
    assert order.order_status == "active"
    assert order.service_name == "Cleaning"
    assert order.suggested_price == 1500


def test_entity_timestamps_follow_orm_updates_and_soft_deletion(session: Session) -> None:
    service = Service(name="Cleaning", description="One hour", suggested_price=1500)
    client = Client(name="Sam", email="sam@example.com", password_hash="hashed")
    session.add_all([service, client])
    session.flush()

    order = Order(
        client_id=client.id,
        service_id=service.id,
        service_name=service.name,
        service_description=service.description,
        suggested_price=service.suggested_price,
    )
    session.add(order)
    session.flush()

    entities = (service, client, order)
    for entity in entities:
        session.refresh(entity)
        assert entity.created_at.utcoffset() == timedelta(0)
        assert entity.updated_at.utcoffset() == timedelta(0)

    original = {entity.id: (entity.created_at, entity.updated_at) for entity in entities}
    service.name = "Deep cleaning"
    client.name = "Samuel"
    order.order_status = "cancel"
    session.flush()

    for entity in entities:
        session.refresh(entity)
        assert entity.created_at == original[entity.id][0]
        assert entity.updated_at > original[entity.id][1]

    before_deletion = {entity.id: entity.updated_at for entity in entities}
    for entity in entities:
        entity.deleted_at = utc_now()
    session.flush()

    for entity in entities:
        session.refresh(entity)
        assert entity.updated_at > before_deletion[entity.id]
        assert entity.deleted_at.utcoffset() == timedelta(0)


def test_sqlmodel_validates_input_and_excludes_password_hash() -> None:
    with pytest.raises(ValidationError):
        Service.model_validate({"name": "Cleaning", "description": "One hour", "suggested_price": 0})
    with pytest.raises(ValidationError):
        Service.model_validate({"name": "", "description": "One hour", "suggested_price": 1500})

    client = Client.model_validate(
        {"name": "Sam", "email": "sam@example.com", "password_hash": "hashed"}
    )
    assert "password_hash" not in client.model_dump()
    assert "hashed" not in repr(client)


@pytest.mark.parametrize(
    ("field", "value"),
    [("name", "  "), ("description", ""), ("suggested_price", 0)],
)
def test_service_rejects_empty_fields_or_nonpositive_price(
    session: Session, field: str, value: str | int
) -> None:
    values = {"name": "Cleaning", "description": "One hour", "suggested_price": 1500}
    values[field] = value
    session.add(Service(**values))

    with pytest.raises(IntegrityError):
        session.flush()


def test_service_name_is_unique_until_soft_deleted(session: Session) -> None:
    service = Service(name="Cleaning", description="One hour", suggested_price=1500)
    session.add(service)
    session.flush()

    session.add(Service(name="Cleaning", description="Two hours", suggested_price=2000))
    with pytest.raises(IntegrityError):
        session.flush()


def test_soft_deleted_service_name_can_be_reused(session: Session) -> None:
    session.add(
        Service(
            name="Cleaning",
            description="One hour",
            suggested_price=1500,
            deleted_at=datetime.now(UTC),
        )
    )
    session.add(Service(name="Cleaning", description="Two hours", suggested_price=2000))
    session.flush()


def test_client_email_is_case_insensitive_and_unique(session: Session) -> None:
    session.add(Client(name="Sam", email="Sam@example.com", password_hash="hashed"))
    session.flush()

    session.add(Client(name="Other", email="sam@EXAMPLE.com", password_hash="hashed"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_soft_deleted_client_email_can_be_reused(session: Session) -> None:
    session.add(
        Client(
            name="Sam",
            email="Sam@example.com",
            password_hash="hashed",
            deleted_at=datetime.now(UTC),
        )
    )
    session.add(Client(name="Other", email="sam@EXAMPLE.com", password_hash="hashed"))
    session.flush()


def test_order_snapshot_does_not_change_with_service(session: Session) -> None:
    service = Service(name="Cleaning", description="One hour", suggested_price=1500)
    client = Client(name="Sam", email="sam@example.com", password_hash="hashed")
    session.add_all([service, client])
    session.flush()

    order = Order(
        client_id=client.id,
        service_id=service.id,
        service_name=service.name,
        service_description=service.description,
        suggested_price=service.suggested_price,
    )
    session.add(order)
    session.flush()

    service.name = "Deep cleaning"
    service.description = "Two hours"
    service.suggested_price = 3000
    session.flush()
    session.refresh(order)

    assert (order.service_name, order.service_description, order.suggested_price) == (
        "Cleaning",
        "One hour",
        1500,
    )


@pytest.mark.parametrize(
    ("field", "value"), [("suggested_price", -1), ("order_status", "other")]
)
def test_order_rejects_invalid_values(session: Session, field: str, value: str | int) -> None:
    service = Service(name="Cleaning", description="One hour", suggested_price=1500)
    client = Client(name="Sam", email="sam@example.com", password_hash="hashed")
    session.add_all([service, client])
    session.flush()

    values = {
        "client_id": client.id,
        "service_id": service.id,
        "service_name": service.name,
        "service_description": service.description,
        "suggested_price": service.suggested_price,
        "order_status": "active",
    }
    values[field] = value
    session.add(Order(**values))

    with pytest.raises(IntegrityError):
        session.flush()
