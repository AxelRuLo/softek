from uuid import UUID

from sqlmodel import Session

from app.orders import Order, OrderCreate, repository


class OrderNotFound(Exception):
    pass


class OrderReferenceNotFound(Exception):
    pass


class OrderAlreadyCancelled(Exception):
    pass


class OrderService:
    def __init__(self, session: Session):
        self.session = session

    def list_orders(self, offset: int, limit: int) -> list[Order]:
        try:
            return repository.list_orders(self.session, offset, limit)
        except Exception:
            self.session.rollback()
            raise

    def get_order(self, order_id: UUID) -> Order:
        try:
            order = repository.get_order(self.session, order_id)
            if order is None:
                raise OrderNotFound
            return order
        except Exception:
            self.session.rollback()
            raise

    def create_order(self, data: OrderCreate) -> Order:
        try:
            client = repository.lock_client(self.session, data.client_id)
            if client is None:
                raise OrderReferenceNotFound
            service = repository.lock_service(self.session, data.service_id)
            if service is None:
                raise OrderReferenceNotFound
            order = Order(
                client_id=client.id,
                service_id=service.id,
                service_name=service.name,
                service_description=service.description,
                suggested_price=service.suggested_price,
            )
            repository.add_order(self.session, order)
            self.session.commit()
            self.session.refresh(order)
            return order
        except Exception:
            self.session.rollback()
            raise

    def cancel_order(self, order_id: UUID) -> Order:
        try:
            order = repository.cancel_order(self.session, order_id)
            if order is None:
                if repository.get_order(self.session, order_id) is None:
                    raise OrderNotFound
                raise OrderAlreadyCancelled
            self.session.commit()
            self.session.refresh(order)
            return order
        except Exception:
            self.session.rollback()
            raise

    def delete_order(self, order_id: UUID) -> None:
        try:
            if not repository.delete_order(self.session, order_id):
                raise OrderNotFound
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
