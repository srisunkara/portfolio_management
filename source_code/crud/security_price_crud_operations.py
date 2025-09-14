# source_code/crud/security_price_crud_operations.py
from typing import List, Optional

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import SecurityPriceDtl, SecurityPriceDtlInput
from source_code.utils import domain_utils as date_utils

class SecurityPriceCRUD(BaseCRUD[SecurityPriceDtl]):
    def __init__(self):
        super().__init__(SecurityPriceDtl)

    def list_all(self) -> List[SecurityPriceDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_price_id, security_id, price_source_id, price_date, price, market_cap, addl_notes, price_currency, created_ts, last_updated_ts "
            "FROM security_price_dtl ORDER BY security_price_id"
        )
        return [SecurityPriceDtl(**row) for row in rows]

    # Save single price (generate ID and timestamps)
    def save(self, item: SecurityPriceDtlInput) -> SecurityPriceDtl:
        next_price_id = date_utils.get_timestamp_with_microseconds()
        now = date_utils.get_current_date_time()
        price = SecurityPriceDtl(
            security_price_id=next_price_id,
            security_id=item.security_id,
            price_source_id=item.price_source_id,
            price_date=item.price_date,
            price=item.price,
            market_cap=item.market_cap,
            addl_notes=item.addl_notes,
            price_currency=item.price_currency,
            created_ts=now,
            last_updated_ts=now,
        )
        sql = """
        INSERT INTO security_price_dtl (
            security_price_id, security_id, price_source_id, price_date, price, market_cap, addl_notes, price_currency, created_ts, last_updated_ts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (security_price_id) DO UPDATE SET
            security_id = EXCLUDED.security_id,
            price_source_id = EXCLUDED.price_source_id,
            price_date = EXCLUDED.price_date,
            price = EXCLUDED.price,
            market_cap = EXCLUDED.market_cap,
            addl_notes = EXCLUDED.addl_notes,
            price_currency = EXCLUDED.price_currency,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            price.security_price_id,
            price.security_id,
            price.price_source_id,
            price.price_date,
            price.price,
            price.market_cap,
            price.addl_notes,
            price.price_currency,
            price.created_ts,
            price.last_updated_ts,
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save security price")
        return price

    # Bulk save multiple inputs
    def save_many(self, items: List[SecurityPriceDtlInput]) -> List[SecurityPriceDtl]:
        result: List[SecurityPriceDtl] = []
        for item in items:
            result.append(self.save(item))
        return result

    def get_security(self, pk: int) -> Optional[SecurityPriceDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_price_id, security_id, price_source_id, price_date, price, market_cap, addl_notes, price_currency, created_ts, last_updated_ts "
            "FROM security_price_dtl WHERE security_price_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return SecurityPriceDtl(**rows[0])

    def update(self, pk: int, item: SecurityPriceDtlInput) -> SecurityPriceDtl:
        # Ensure exists
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("Security price not found")

        sql = """
        UPDATE security_price_dtl
        SET
            security_id = %s,
            price_source_id = %s,
            price_date = %s,
            price = %s,
            market_cap = %s,
            addl_notes = %s,
            price_currency = %s,
            last_updated_ts = %s
        WHERE security_price_id = %s
        """
        params = (
            item.security_id,
            item.price_source_id,
            item.price_date,
            item.price,
            item.market_cap,
            item.addl_notes,
            item.price_currency,
            date_utils.get_current_date_time(),
            pk,
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Security price not found")
        return self.get_security(pk)

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM security_price_dtl WHERE security_price_id = %s",
            (pk,),
        )
        return affected > 0

# Keep a singleton instance for importers (routes)
security_price_crud = SecurityPriceCRUD()
