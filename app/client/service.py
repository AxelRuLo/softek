from uuid import UUID

from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.client import Client, ClientCreate, repository
from app.timestamps import utc_now

_password_hasher = PasswordHasher()


class ClientNotFound(Exception):
    pass


class ClientEmailConflict(Exception):
    pass


class ClientService:
    def __init__(self, session: Session):
        self.session = session

    def get_client(self, client_id: UUID) -> Client:
        client = repository.get(self.session, client_id)
        if client is None:
            raise ClientNotFound
        return client

    def list_clients(self, offset: int = 0, limit: int = 20) -> list[Client]:
        return repository.list_active(self.session, offset, limit)

    def create_client(self, data: ClientCreate) -> Client:
        client = Client(name=data.name, email=data.email, password_hash=_password_hasher.hash(data.password))
        try:
            repository.add(self.session, client)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if repository.email_exists(self.session, data.email):
                raise ClientEmailConflict from None
            raise
        except Exception:
            self.session.rollback()
            raise
        return client

    def update_client(self, client_id: UUID, values: dict) -> Client:
        try:
            client = self.get_client(client_id)
            values = values.copy()
            if "password" in values:
                values["password_hash"] = _password_hasher.hash(values.pop("password"))
            if not values:
                return client
            client = repository.update_active(self.session, client_id, values)
            if client is None:
                raise ClientNotFound
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if "email" in values and repository.email_exists(self.session, values["email"], client_id):
                raise ClientEmailConflict from None
            raise
        except Exception:
            self.session.rollback()
            raise
        return client

    def delete_client(self, client_id: UUID) -> None:
        try:
            if not repository.soft_delete(self.session, client_id, utc_now()):
                raise ClientNotFound
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
