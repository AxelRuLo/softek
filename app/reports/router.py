from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.reports import ClientSales, RecentSale, ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service(session: Annotated[Session, Depends(get_session)]) -> ReportService:
    return ReportService(session)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


@router.get("/sales/recent", response_model=list[RecentSale])
def recent_sales(report_service: ReportServiceDep):
    return report_service.recent_sales()


@router.get("/sales/by-client", response_model=list[ClientSales])
def sales_by_client(
    report_service: ReportServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return report_service.sales_by_client(offset, limit)
