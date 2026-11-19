"""Service business operations, independent of HTTP."""

from contextlib import contextmanager
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.service import Service, repository
from app.timestamps import utc_now


class ServiceNotFound(Exception):
    pass


class ServiceNameConflict(Exception):
    pass


class ServiceManager:
    def __init__(self, session: Session):
        self.session = session

    @contextmanager
    def _transaction(self):
        try:
            yield
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            original = exc.orig
            constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
            if constraint == "uq_services_active_name" or "UNIQUE constraint failed: services.name" in str(original):
                raise ServiceNameConflict from exc
            raise
        except Exception:
            self.session.rollback()
            raise

    def get_service(self, service_id: UUID) -> Service:
        item = repository.get_active(self.session, service_id)
        if item is None:
            raise ServiceNotFound
        return item

    def list_services(self, offset: int, limit: int) -> list[Service]:
        return repository.list_active(self.session, offset, limit)

    def create_service(self, values: dict) -> Service:
        with self._transaction():
            item = repository.save(self.session, Service(**values))
        self.session.refresh(item)
        return item

    def update_service(self, service_id: UUID, values: dict) -> Service:
        with self._transaction():
            item = repository.update_active(self.session, service_id, values)
            if item is None:
                raise ServiceNotFound
        self.session.refresh(item)
        return item

    def delete_service(self, service_id: UUID) -> None:
        with self._transaction():
            if not repository.delete_active(self.session, service_id, utc_now()):
                raise ServiceNotFound
