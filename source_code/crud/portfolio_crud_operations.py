from typing import List, Optional

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import PortfolioDtl, PortfolioDtlInput
from source_code.utils import domain_utils as date_utils


class PortfolioCRUD(BaseCRUD[PortfolioDtl]):
    def __init__(self):
        super().__init__(PortfolioDtl)

    # Override list_all to fetch from the DB (keeps routes unchanged)
    def list_all(self) -> List[PortfolioDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT portfolio_id, user_id, name, open_date, close_date, created_ts, last_updated_ts "
            "FROM portfolio_dtl ORDER BY portfolio_id"
        )
        return [PortfolioDtl(**row) for row in rows]

    # Optional named method for symmetry
    def list_portfolios(self) -> List[PortfolioDtl]:
        return self.list_all()

    # Save a single portfolio using input model (generate id + timestamps)
    def save(self, item: PortfolioDtlInput) -> PortfolioDtl:
        next_portfolio_id = date_utils.get_timestamp_with_microseconds()
        pf = PortfolioDtl(
            portfolio_id=next_portfolio_id,
            user_id=item.user_id,
            name=item.name,
            open_date=item.open_date,
            close_date=item.close_date,
            created_ts=date_utils.get_current_date_time(),
            last_updated_ts=date_utils.get_current_date_time(),
        )
        sql = """
        INSERT INTO portfolio_dtl (
            portfolio_id, user_id, name, open_date, close_date, created_ts, last_updated_ts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (portfolio_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            name = EXCLUDED.name,
            open_date = EXCLUDED.open_date,
            close_date = EXCLUDED.close_date,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            pf.portfolio_id, pf.user_id, pf.name, pf.open_date, pf.close_date,
            pf.created_ts, pf.last_updated_ts
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save portfolio")
        return pf

    # Bulk save list of portfolio inputs
    def save_many(self, items: List[PortfolioDtlInput]) -> List[PortfolioDtl]:
        result: List[PortfolioDtl] = []
        for item in items:
            result.append(self.save(item))
        return result

    # Override get to fetch from DB (method name kept for compatibility with routes)
    def get_security(self, pk: int) -> Optional[PortfolioDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT portfolio_id, user_id, name, open_date, close_date, created_ts, last_updated_ts "
            "FROM portfolio_dtl WHERE portfolio_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return PortfolioDtl(**rows[0])

    # Update to persist changes to DB using input model; id comes from path
    def update(self, pk: int, item: PortfolioDtlInput) -> PortfolioDtl:
        # Ensure the portfolio exists
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("Portfolio not found")

        now = date_utils.get_current_date_time()
        sql = """
        UPDATE portfolio_dtl
        SET
            user_id = %s,
            name = %s,
            open_date = %s,
            close_date = %s,
            last_updated_ts = %s
        WHERE portfolio_id = %s
        """
        params = (
            item.user_id, item.name, item.open_date, item.close_date,
            now, pk
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Portfolio not found")
        # Return latest from DB
        return self.get_security(pk)

    # Override delete to remove from DB
    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM portfolio_dtl WHERE portfolio_id = %s",
            (pk,),
        )
        return affected > 0


# Keep a singleton instance for importers (routes)
portfolio_crud = PortfolioCRUD()
