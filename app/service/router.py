from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.database import get_session
from app.service import service
from app.service.schemas import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


def get_service_manager(
    session: Annotated[Session, Depends(get_session)],
) -> service.ServiceManager:
    return service.ServiceManager(session)


ServiceDep = Annotated[service.ServiceManager, Depends(get_service_manager)]


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate, manager: ServiceDep):
    try:
        return manager.create_service(payload.model_dump())
    except service.ServiceNameConflict as exc:
        raise HTTPException(
            status_code=409, detail="Service name already exists"
        ) from exc


@router.get("", response_model=list[ServiceRead])
def list_services(
    manager: ServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return manager.list_services(offset, limit)


@router.get("/{service_id}", response_model=ServiceRead)
def get_service(service_id: UUID, manager: ServiceDep):
    try:
        return manager.get_service(service_id)
    except service.ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail="Service not found") from exc


def _update(service_id: UUID, values: dict, manager: service.ServiceManager):
    try:
        return manager.update_service(service_id, values)
    except service.ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail="Service not found") from exc
    except service.ServiceNameConflict as exc:
        raise HTTPException(
            status_code=409, detail="Service name already exists"
        ) from exc


@router.put("/{service_id}", response_model=ServiceRead)
def replace_service(service_id: UUID, payload: ServiceCreate, manager: ServiceDep):
    return _update(service_id, payload.model_dump(), manager)


@router.patch("/{service_id}", response_model=ServiceRead)
def update_service(service_id: UUID, payload: ServiceUpdate, manager: ServiceDep):
    return _update(service_id, payload.model_dump(exclude_unset=True), manager)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: UUID, manager: ServiceDep) -> Response:
    try:
        manager.delete_service(service_id)
    except service.ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail="Service not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
