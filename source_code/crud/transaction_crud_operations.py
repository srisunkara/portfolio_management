from typing import List, Optional

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import TransactionDtl, TransactionDtlInput, TransactionFullView
from source_code.utils import domain_utils as date_utils


class TransactionCRUD(BaseCRUD[TransactionDtl]):
    def __init__(self):
        super().__init__(TransactionDtl)

    @staticmethod
    def _normalize_type(ttype: Optional[str]) -> str:
        from source_code.models.models import TRANSACTION_TYPES
        if ttype is None:
            return "B"
        s = str(ttype).strip()
        if not s:
            return "B"
        u = s.upper()
        if u in TRANSACTION_TYPES:
            return u
        # allow labels like "Buy"/"Sell"
        rev = {v.upper(): k for k, v in TRANSACTION_TYPES.items()}
        if u in rev:
            return rev[u]
        raise ValueError("Invalid transaction_type; expected one of: " + ", ".join(list(TRANSACTION_TYPES.keys())))

    def list_full(self) -> List[TransactionFullView]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT * FROM v_transaction_full ORDER BY transaction_id"
        )
        return [TransactionFullView(**row) for row in rows]

    # Bulk save JSON array
    def save_many(self, items: List[TransactionDtlInput]) -> List[TransactionDtl]:
        results: List[TransactionDtl] = []
        for it in items:
            results.append(self.save(it))
        return results

    def list_all(self) -> List[TransactionDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT transaction_id, portfolio_id, security_id, external_platform_id, transaction_date, transaction_type, "
            "transaction_qty, transaction_price, transaction_fee, transaction_fee_percent, carry_fee, carry_fee_percent, "
            "management_fee, management_fee_percent, external_manager_fee, external_manager_fee_percent, created_ts, last_updated_ts "
            "FROM transaction_dtl ORDER BY transaction_id"
        )
        return [TransactionDtl(**row) for row in rows]

    def save(self, item: TransactionDtlInput) -> TransactionDtl:
        # Generate server-side ID and timestamps
        next_id = date_utils.get_timestamp_with_microseconds()
        now = date_utils.get_current_date_time()
        txn = TransactionDtl(
            transaction_id=next_id,
            portfolio_id=item.portfolio_id,
            security_id=item.security_id,
            external_platform_id=item.external_platform_id,
            transaction_date=item.transaction_date,
            transaction_type=self._normalize_type(item.transaction_type),
            transaction_qty=item.transaction_qty,
            transaction_price=item.transaction_price,
            transaction_fee=item.transaction_fee,
            transaction_fee_percent=item.transaction_fee_percent,
            carry_fee=item.carry_fee,
            carry_fee_percent=item.carry_fee_percent,
            management_fee=item.management_fee,
            management_fee_percent=item.management_fee_percent,
            external_manager_fee=item.external_manager_fee,
            external_manager_fee_percent=item.external_manager_fee_percent,
            created_ts=now,
            last_updated_ts=now,
        )
        sql = """
        INSERT INTO transaction_dtl (
            transaction_id, portfolio_id, security_id, external_platform_id, transaction_date, transaction_type,
            transaction_qty, transaction_price, transaction_fee, transaction_fee_percent,
            carry_fee, carry_fee_percent, management_fee, management_fee_percent,
            external_manager_fee, external_manager_fee_percent, created_ts, last_updated_ts
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (transaction_id) DO UPDATE SET
            portfolio_id = EXCLUDED.portfolio_id,
            security_id = EXCLUDED.security_id,
            external_platform_id = EXCLUDED.external_platform_id,
            transaction_date = EXCLUDED.transaction_date,
            transaction_type = EXCLUDED.transaction_type,
            transaction_qty = EXCLUDED.transaction_qty,
            transaction_price = EXCLUDED.transaction_price,
            transaction_fee = EXCLUDED.transaction_fee,
            transaction_fee_percent = EXCLUDED.transaction_fee_percent,
            carry_fee = EXCLUDED.carry_fee,
            carry_fee_percent = EXCLUDED.carry_fee_percent,
            management_fee = EXCLUDED.management_fee,
            management_fee_percent = EXCLUDED.management_fee_percent,
            external_manager_fee = EXCLUDED.external_manager_fee,
            external_manager_fee_percent = EXCLUDED.external_manager_fee_percent,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            txn.transaction_id, txn.portfolio_id, txn.security_id, txn.external_platform_id, txn.transaction_date,
            txn.transaction_type,
            txn.transaction_qty, txn.transaction_price, txn.transaction_fee, txn.transaction_fee_percent,
            txn.carry_fee, txn.carry_fee_percent, txn.management_fee, txn.management_fee_percent,
            txn.external_manager_fee, txn.external_manager_fee_percent, txn.created_ts, txn.last_updated_ts
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save transaction")
        return txn

    def get_security(self, pk: int) -> Optional[TransactionDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT transaction_id, portfolio_id, security_id, external_platform_id, transaction_date, transaction_type, "
            "transaction_qty, transaction_price, transaction_fee, transaction_fee_percent, "
            "carry_fee, carry_fee_percent, management_fee, management_fee_percent, "
            "external_manager_fee, external_manager_fee_percent, created_ts, last_updated_ts "
            "FROM transaction_dtl WHERE transaction_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return TransactionDtl(**rows[0])

    # Alias for clarity in routes
    def get_transaction(self, pk: int) -> Optional[TransactionDtl]:
        return self.get_security(pk)

    def update(self, pk: int, item: TransactionDtlInput) -> TransactionDtl:
        # Ensure exists
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("Transaction not found")
        now = date_utils.get_current_date_time()
        sql = """
        UPDATE transaction_dtl
        SET
            portfolio_id = %s,
            security_id = %s,
            external_platform_id = %s,
            transaction_date = %s,
            transaction_type = %s,
            transaction_qty = %s,
            transaction_price = %s,
            transaction_fee = %s,
            transaction_fee_percent = %s,
            carry_fee = %s,
            carry_fee_percent = %s,
            management_fee = %s,
            management_fee_percent = %s,
            external_manager_fee = %s,
            external_manager_fee_percent = %s,
            last_updated_ts = %s
        WHERE transaction_id = %s
        """
        params = (
            item.portfolio_id,
            item.security_id,
            item.external_platform_id,
            item.transaction_date,
            self._normalize_type(item.transaction_type),
            item.transaction_qty,
            item.transaction_price,
            item.transaction_fee,
            item.transaction_fee_percent,
            item.carry_fee,
            item.carry_fee_percent,
            item.management_fee,
            item.management_fee_percent,
            item.external_manager_fee,
            item.external_manager_fee_percent,
            now,
            pk,
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Transaction not found")
        # Return latest from DB
        return self.get_security(pk)

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM transaction_dtl WHERE transaction_id = %s",
            (pk,),
        )
        return affected > 0


# Keep a singleton instance for importers (routes)
transaction_crud = TransactionCRUD()
