# source_code/crud/user_crud_operations.py
from typing import Optional, List

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import UserDtl, UserDtlInput
from source_code.utils import domain_utils as date_utils


class UserCRUD(BaseCRUD[UserDtl]):
    def __init__(self):
        super().__init__(UserDtl)

    def list_all(self) -> List[UserDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT user_id, first_name, last_name, email, password_hash, created_ts, last_updated_ts "
            "FROM user_dtl ORDER BY user_id"
        )
        return [UserDtl(**row) for row in rows]

    def save(self, item: UserDtlInput) -> UserDtl:
        # Generate ID and timestamps server-side.
        next_id = date_utils.get_timestamp_with_microseconds()
        now = date_utils.get_current_date_time()
        # We expect routes to pass hashed password in item.password if provided; map to password_hash
        password_hash = item.password if getattr(item, 'password', None) else None
        user = UserDtl(
            user_id=next_id,
            first_name=item.first_name,
            last_name=item.last_name,
            email=item.email,
            password_hash=password_hash,
            created_ts=now,
            last_updated_ts=now,
        )
        columns = ["user_id", "first_name", "last_name", "created_ts", "last_updated_ts"]
        values = [user.user_id, user.first_name, user.last_name, user.created_ts, user.last_updated_ts]
        if user.email is not None:
            columns.insert(3, "email")
            values.insert(3, user.email)
        if user.password_hash is not None:
            insert_pos = 4 if user.email is not None else 3
            columns.insert(insert_pos, "password_hash")
            values.insert(insert_pos, user.password_hash)
        placeholders = ", ".join(["%s"] * len(values))
        update_assignments = [
            "first_name = EXCLUDED.first_name",
            "last_name = EXCLUDED.last_name",
            "last_updated_ts = EXCLUDED.last_updated_ts",
        ]
        if user.email is not None:
            update_assignments.insert(2, "email = EXCLUDED.email")
        if user.password_hash is not None:
            update_assignments.insert(3, "password_hash = EXCLUDED.password_hash")
        sql = f"""
        INSERT INTO user_dtl ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (user_id) DO UPDATE SET
            {", ".join(update_assignments)}
        """
        affected = pg_db_conn_manager.execute_query(sql, tuple(values))
        if affected == 0:
            raise RuntimeError("Failed to save user")
        return user

    def get_security(self, pk: int) -> Optional[UserDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT user_id, first_name, last_name, email, password_hash, created_ts, last_updated_ts "
            "FROM user_dtl WHERE user_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return UserDtl(**rows[0])

    def update(self, pk: int, item: UserDtlInput) -> UserDtl:
        # Ensure exists
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("User not found")

        now = date_utils.get_current_date_time()
        # Map optional password from input to password_hash; if not provided, keep existing
        new_password_hash = item.password if getattr(item, 'password', None) else existing.password_hash
        sql = """
        UPDATE user_dtl
        SET
            first_name = %s,
            last_name = %s,
            email = %s,
            password_hash = %s,
            last_updated_ts = %s
        WHERE user_id = %s
        """
        params = (item.first_name, item.last_name, item.email, new_password_hash, now, pk)
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("User not found")
        # Return latest from DB
        return self.get_security(pk)

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM user_dtl WHERE user_id = %s",
            (pk,),
        )
        return affected > 0

    # Bulk save
    def save_many(self, items: List[UserDtlInput]) -> List[UserDtl]:
        results: List[UserDtl] = []
        for it in items:
            results.append(self.save(it))
        return results

    # Add User-specific operations here if needed
    def get_by_email(self, email: str) -> Optional[UserDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT user_id, first_name, last_name, email, password_hash, created_ts, last_updated_ts "
            "FROM user_dtl WHERE email = %s LIMIT 1",
            (email,),
        )
        if not rows:
            return None
        return UserDtl(**rows[0])


# Keep a singleton instance for importers (routes)
user_crud = UserCRUD()
