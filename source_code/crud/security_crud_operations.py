# source_code/crud/security_crud.py
from typing import List, Optional

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import SecurityDtl, SecurityDtlInput
from source_code.utils import domain_utils as date_utils


class SecurityCRUD(BaseCRUD[SecurityDtl]):
    def __init__(self):
        super().__init__(SecurityDtl)

    def list_all(self) -> List[SecurityDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_id, ticker, name, company_name, security_currency, is_private, created_ts, last_updated_ts "
            "FROM security_dtl ORDER BY ticker, name, security_id"
        )
        return [SecurityDtl(**row) for row in rows]

    def list_all_public(self) -> List[SecurityDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_id, ticker, name, company_name, security_currency, is_private, created_ts, last_updated_ts "
            "FROM security_dtl where is_private = False "
            "ORDER BY ticker, name, security_id"
        )
        return [SecurityDtl(**row) for row in rows]

    def save(self, item: SecurityDtlInput) -> SecurityDtl:
        next_security_id = date_utils.get_timestamp_with_microseconds()
        sec_dtl = SecurityDtl(
            security_id=next_security_id,
            ticker=item.ticker,
            name=item.name,
            company_name=item.company_name,
            security_currency=item.security_currency,
            is_private=item.is_private,
            created_ts=date_utils.get_current_date_time(),
            last_updated_ts=date_utils.get_current_date_time(),
        )
        sql = """
        INSERT INTO security_dtl (
            security_id, ticker, name, company_name, security_currency, is_private, created_ts, last_updated_ts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (security_id) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            name = EXCLUDED.name,
            company_name = EXCLUDED.company_name,
            security_currency = EXCLUDED.security_currency,
            is_private = EXCLUDED.is_private,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            sec_dtl.security_id, sec_dtl.ticker, sec_dtl.name, sec_dtl.company_name,
            sec_dtl.security_currency.upper(), sec_dtl.is_private,
            sec_dtl.created_ts, sec_dtl.last_updated_ts
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save security")

        return sec_dtl

    # Bulk save multiple SecurityDtlInput items
    def save_many(self, items: List[SecurityDtlInput]) -> List[SecurityDtl]:
        results: List[SecurityDtl] = []
        for item in items:
            results.append(self.save(item))
        return results

    def get_security(self, pk: int) -> Optional[SecurityDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_id, ticker, name, company_name, security_currency, is_private, created_ts, last_updated_ts "
            "FROM security_dtl WHERE security_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return SecurityDtl(**rows[0])

    def update(self, pk: int, item: SecurityDtl) -> SecurityDtl:
        # get security by id
        existing_security = self.get_security(pk=pk)
        if not existing_security:
            raise KeyError("Security not found")

        if existing_security.security_id != pk:
            raise ValueError(f"Path security_id={pk} does not match body security_id={item.security_id}")

        sql = """
        UPDATE security_dtl
        SET
            ticker = %s,
            name = %s,
            company_name = %s,
            security_currency = %s,
            is_private = %s,
            last_updated_ts = %s
        WHERE security_id = %s
        """
        params = (
            item.ticker, item.name, item.company_name, item.security_currency.upper(), item.is_private, date_utils.get_current_date_time(), pk
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Security not found")
        # get latest security from DB and return
        existing_security = self.get_security(pk=pk)
        return existing_security

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM security_dtl WHERE security_id = %s",
            (pk,),
        )
        return affected > 0

# Keep a singleton instance for importers (routes)
security_crud = SecurityCRUD()
