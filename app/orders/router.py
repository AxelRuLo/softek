from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.database import get_session
from app.orders import service, OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(
    session: Annotated[Session, Depends(get_session)],
) -> service.OrderService:
    return service.OrderService(session)


OrderServiceDep = Annotated[service.OrderService, Depends(get_order_service)]


@router.get("", response_model=list[OrderRead])
def list_orders(
    order_service: OrderServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return order_service.list_orders(offset, limit)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: UUID, order_service: OrderServiceDep):
    try:
        return order_service.get_order(order_id)
    except service.OrderNotFound as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, order_service: OrderServiceDep):
    try:
        return order_service.create_order(data)
    except service.OrderReferenceNotFound as exc:
        raise HTTPException(
            status_code=404, detail="Client or service not found"
        ) from exc


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: UUID, order_service: OrderServiceDep):
    try:
        return order_service.cancel_order(order_id)
    except service.OrderNotFound as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    except service.OrderAlreadyCancelled as exc:
        raise HTTPException(status_code=409, detail="Order already cancelled") from exc


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: UUID, order_service: OrderServiceDep) -> Response:
    try:
        order_service.delete_order(order_id)
    except service.OrderNotFound as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
