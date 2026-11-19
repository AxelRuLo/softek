from sqlmodel import Session

from app.reports import ClientSales, RecentSale, repository


class ReportService:
    def __init__(self, session: Session):
        self.session = session

    def recent_sales(self) -> list[RecentSale]:
        try:
            return repository.recent_sales(self.session)
        except Exception:
            self.session.rollback()
            raise

    def sales_by_client(self, offset: int, limit: int) -> list[ClientSales]:
        try:
            return repository.sales_by_client(self.session, offset, limit)
        except Exception:
            self.session.rollback()
            raise
