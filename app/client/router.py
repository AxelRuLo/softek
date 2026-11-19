from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.client import service, ClientCreate, ClientRead,ClientUpdate
from app.database import get_session

router = APIRouter(prefix="/clients", tags=["clients"])

def get_client_service(session: Annotated[Session, Depends(get_session)]) -> service.ClientService:
    return service.ClientService(session)


ClientServiceDep = Annotated[service.ClientService, Depends(get_client_service)]


@router.get("", response_model=list[ClientRead])
def list_clients(
    client_service: ClientServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return client_service.list_clients(offset, limit)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, client_service: ClientServiceDep):
    try:
        return client_service.create_client(data)
    except service.ClientEmailConflict as exc:
        raise HTTPException(status_code=409, detail="Client email already exists") from exc


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: UUID, client_service: ClientServiceDep):
    try:
        return client_service.get_client(client_id)
    except service.ClientNotFound as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc


def _update(client_id: UUID, values: dict, client_service: service.ClientService):
    try:
        return client_service.update_client(client_id, values)
    except service.ClientNotFound as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    except service.ClientEmailConflict as exc:
        raise HTTPException(status_code=409, detail="Client email already exists") from exc


@router.put("/{client_id}", response_model=ClientRead)
def replace_client(client_id: UUID, data: ClientCreate, client_service: ClientServiceDep):
    return _update(client_id, data.model_dump(), client_service)


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(client_id: UUID, data: ClientUpdate, client_service: ClientServiceDep):
    return _update(client_id, data.model_dump(exclude_unset=True), client_service)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: UUID, client_service: ClientServiceDep):
    try:
        client_service.delete_client(client_id)
    except service.ClientNotFound as exc:
        raise HTTPException(status_code=404, detail="Client not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
