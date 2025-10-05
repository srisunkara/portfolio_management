# source_code/crud/holding_crud_operations.py
from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from typing import List, Optional

from source_code.models.models import HoldingDtl, HoldingDtlInput
from source_code.utils import domain_utils as date_utils


# def list_holdings():
#     # data = DatabaseConfig().execute_query(query="SELECT * FROM holding")
#     data = pg_db_conn_manager.fetch_data(query="SELECT * FROM holding_dtl")
#     return data


class HoldingCRUD(BaseCRUD[HoldingDtl]):
    def __init__(self):
        super().__init__(HoldingDtl)

    # Uniform list_all like other modules
    def list_all(self) -> List[HoldingDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT holding_id, holding_dt, portfolio_id, security_id, quantity, price, avg_price, market_value, created_ts, last_updated_ts "
            "FROM holding_dtl ORDER BY holding_id"
        )
        return [HoldingDtl(**row) for row in rows]

    # Keep existing alias used by routes (delegates to list_all)
    def list_holdings(self) -> List[HoldingDtl]:
        return self.list_all()

    # Save a single holding from input; generate id and timestamps
    def save(self, item: HoldingDtlInput) -> HoldingDtl:
        next_holding_id = date_utils.get_timestamp_with_microseconds()
        now = date_utils.get_current_date_time()
        h = HoldingDtl(
            holding_id=next_holding_id,
            holding_dt=item.holding_dt,
            portfolio_id=item.portfolio_id,
            security_id=item.security_id,
            quantity=item.quantity,
            price=item.price,
            avg_price=item.avg_price,
            market_value=item.market_value,
            created_ts=now,
            last_updated_ts=now,
        )
        sql = """
        INSERT INTO holding_dtl (
            holding_id, holding_dt, portfolio_id, security_id, quantity, price, avg_price, market_value, created_ts, last_updated_ts
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (holding_id) DO UPDATE SET
            holding_dt = EXCLUDED.holding_dt,
            portfolio_id = EXCLUDED.portfolio_id,
            security_id = EXCLUDED.security_id,
            quantity = EXCLUDED.quantity,
            price = EXCLUDED.price,
            avg_price = EXCLUDED.avg_price,
            market_value = EXCLUDED.market_value,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            h.holding_id, h.holding_dt, h.portfolio_id, h.security_id,
            h.quantity, h.price, h.avg_price, h.market_value, h.created_ts, h.last_updated_ts
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save holding")
        return h

    # Bulk save multiple HoldingDtlInput items
    def save_many(self, items: List[HoldingDtlInput]) -> List[HoldingDtl]:
        result: List[HoldingDtl] = []
        for item in items:
            result.append(self.save(item))
        return result

    # Override BaseCRUD.get to read from DB
    def get_security(self, pk: int) -> Optional[HoldingDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT holding_id, holding_dt, portfolio_id, security_id, quantity, price, avg_price, market_value, created_ts, last_updated_ts "
            "FROM holding_dtl WHERE holding_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return HoldingDtl(**rows[0])

    # Update: set last_updated_ts to now
    def update(self, pk: int, item: HoldingDtlInput) -> HoldingDtl:
        if item.holding_id != pk:
            raise ValueError(f"Path holding_id={pk} does not match body holding_id={item.holding_id}")

        sql = """
        UPDATE holding_dtl
        SET
            holding_dt = %s,
            portfolio_id = %s,
            security_id = %s,
            quantity = %s,
            price = %s,
            avg_price = %s,
            market_value = %s,
            last_updated_ts = %s
        WHERE holding_id = %s
        """
        params = (
            item.holding_dt, item.portfolio_id, item.security_id, item.quantity,
            item.price, item.avg_price, item.market_value, date_utils.get_current_date_time(), pk
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Holding not found")
        # Return latest row
        return self.get_security(pk)

    # Override BaseCRUD.delete to delete from DB
    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM holding_dtl WHERE holding_id = %s",
            (pk,),
        )
        return affected > 0

    def recalc_for_date(self, target_date) -> dict:
        """
        Recalculate holdings for a given date by aggregating transactions up to and including that date.
        Computes net quantity and moving average cost (avg_price) for each (portfolio_id, security_id).
        Sets price from security_price_dtl for that date if available; market_value = quantity * price.
        Replaces existing holdings for the target_date.
        Returns summary dict {"deleted": n, "inserted": m}.
        """
        # Fetch transactions up to date
        rows = pg_db_conn_manager.fetch_data(
            """
            SELECT portfolio_id, security_id, transaction_date, transaction_type, transaction_qty, transaction_price
            FROM transaction_dtl
            WHERE transaction_date <= %s
            ORDER BY portfolio_id, security_id, transaction_date, transaction_id
            """,
            (target_date,)
        )
        # Aggregate by moving average
        from collections import defaultdict
        agg = defaultdict(lambda: {"qty": 0.0, "avg": 0.0})
        for r in rows:
            key = (r["portfolio_id"], r["security_id"])
            qty = float(r["transaction_qty"] or 0.0)
            price = float(r["transaction_price"] or 0.0)
            ttype = str(r["transaction_type"]).upper()
            cur_qty = agg[key]["qty"]
            cur_avg = agg[key]["avg"]
            if ttype in ("B", "BUY"):
                new_qty = cur_qty + qty
                # Avoid division by zero
                if new_qty > 0:
                    new_avg = ((cur_qty * cur_avg) + (qty * price)) / new_qty
                else:
                    new_avg = 0.0
                agg[key]["qty"] = new_qty
                agg[key]["avg"] = new_avg
            elif ttype in ("S", "SELL"):
                new_qty = cur_qty - qty
                agg[key]["qty"] = new_qty
                # avg cost unchanged on sell; if position closed, reset avg to 0
                if new_qty <= 0:
                    agg[key]["avg"] = 0.0
            else:
                # Unknown type — ignore
                continue
        # Remove zero or negative positions
        holdings = [(pid, sid, round(vals["qty"], 6), float(vals["avg"])) for (pid, sid), vals in agg.items() if vals["qty"] > 0]

        # Delete existing for date
        deleted = pg_db_conn_manager.execute_query(
            "DELETE FROM holding_dtl WHERE holding_dt = %s",
            (target_date,)
        )

        # Insert new holdings
        inserted = 0
        if holdings:
            for (pid, sid, qty, avg_cost) in holdings:
                # Price on date if exists
                price_rows = pg_db_conn_manager.fetch_data(
                    "SELECT price FROM security_price_dtl WHERE security_id = %s AND price_date = %s ORDER BY security_price_id DESC LIMIT 1",
                    (sid, target_date)
                )
                price = float(price_rows[0]["price"]) if price_rows else 0.0
                market_value = round(qty * price, 2)
                now = date_utils.get_current_date_time()
                hid = date_utils.get_timestamp_with_microseconds()
                pg_db_conn_manager.execute_query(
                    """
                    INSERT INTO holding_dtl (holding_id, holding_dt, portfolio_id, security_id, quantity, price, avg_price, market_value, created_ts, last_updated_ts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (holding_id) DO NOTHING
                    """,
                    (hid, target_date, pid, sid, qty, price, avg_cost, market_value, now, now)
                )
                inserted += 1
        return {"deleted": int(deleted), "inserted": int(inserted)}


# Keep a singleton instance for importers (routes)
holding_crud = HoldingCRUD()
