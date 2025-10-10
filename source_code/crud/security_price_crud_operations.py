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
            "SELECT security_price_id, price_dtl.security_id, price_source_id, price_date,  "
            "price, market_cap, addl_notes, price_currency, price_dtl.created_ts, price_dtl.last_updated_ts "
            "FROM security_price_dtl price_dtl "
            "inner join security_dtl on price_dtl.security_id = security_dtl.security_id "
            "ORDER BY ticker, name, security_id"
        )
        return [SecurityPriceDtl(**row) for row in rows]

    def list_by_date(self, target_date) -> List[SecurityPriceDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_price_id, price_dtl.security_id, price_source_id, price_date,  "
            "price, market_cap, addl_notes, price_currency, price_dtl.created_ts, price_dtl.last_updated_ts "
            "FROM security_price_dtl price_dtl "
            "inner join security_dtl on price_dtl.security_id = security_dtl.security_id "
            "WHERE price_date = %s "
            "ORDER BY ticker, name, security_id",
            (target_date,)
        )
        return [SecurityPriceDtl(**row) for row in rows]

    def list_by_date_range_and_ticker(self, from_date=None, to_date=None, ticker=None) -> List[SecurityPriceDtl]:
        """Get security prices filtered by date range and/or ticker"""
        # Build dynamic query based on provided filters
        conditions = []
        params = []
        
        if from_date is not None:
            conditions.append("price_date >= %s")
            params.append(from_date)
            
        if to_date is not None:
            conditions.append("price_date <= %s")
            params.append(to_date)
            
        if ticker is not None:
            conditions.append("upper(ticker) = %s")
            params.append(ticker.strip().upper())
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        query = (
            "SELECT security_price_id, price_dtl.security_id, price_source_id, price_date,  "
            "price, market_cap, addl_notes, price_currency, price_dtl.created_ts, price_dtl.last_updated_ts "
            "FROM security_price_dtl price_dtl "
            "inner join security_dtl on price_dtl.security_id = security_dtl.security_id "
            f"{where_clause} "
            "ORDER BY price_date ASC, ticker, name, security_id"
        )
        
        rows = pg_db_conn_manager.fetch_data(query, tuple(params))
        return [SecurityPriceDtl(**row) for row in rows]

    def get_price_by_ticker_and_date(self, ticker: str, price_date) -> Optional[SecurityPriceDtl]:
        """Get security price for a specific ticker and date"""
        rows = pg_db_conn_manager.fetch_data(
            "SELECT security_price_id, price_dtl.security_id, price_source_id, price_date,  "
            "price, market_cap, addl_notes, price_currency, price_dtl.created_ts, price_dtl.last_updated_ts "
            "FROM security_price_dtl price_dtl "
            "inner join security_dtl on price_dtl.security_id = security_dtl.security_id "
            "WHERE ticker = %s AND price_date = %s "
            "ORDER BY price_dtl.last_updated_ts DESC LIMIT 1",
            (ticker, price_date)
        )
        if not rows:
            return None
        return SecurityPriceDtl(**rows[0])

    # Save single price (generate ID and timestamps) with natural-key upsert
    # Natural key: (security_id, price_source_id, price_date)
    # If a row already exists for this combination, update it instead of inserting a duplicate.
    def save(self, item: SecurityPriceDtlInput) -> SecurityPriceDtl:
        # Check if a price already exists for the same security/source/date
        existing_rows = pg_db_conn_manager.fetch_data(
            "SELECT security_price_id FROM security_price_dtl WHERE security_id = %s AND price_source_id = %s AND price_date = %s LIMIT 1",
            (item.security_id, item.price_source_id, item.price_date),
        )
        now = date_utils.get_current_date_time()
        if existing_rows:
            # Update existing row
            existing_id = existing_rows[0]["security_price_id"]
            update_sql = (
                "UPDATE security_price_dtl\n"
                "SET price = %s,\n"
                "    market_cap = %s,\n"
                "    addl_notes = %s,\n"
                "    price_currency = %s,\n"
                "    last_updated_ts = %s\n"
                "WHERE security_price_id = %s"
            )
            params = (
                item.price,
                item.market_cap,
                item.addl_notes,
                item.price_currency,
                now,
                existing_id,
            )
            affected = pg_db_conn_manager.execute_query(update_sql, params)
            if affected == 0:
                raise RuntimeError("Failed to update security price")
            return self.get_security(existing_id)
        # Else insert new row
        next_price_id = date_utils.get_timestamp_with_microseconds()
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
        insert_sql = """
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
        affected = pg_db_conn_manager.execute_query(insert_sql, params)
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
