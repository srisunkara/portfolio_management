from typing import List, Optional

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import ExternalPlatformDtl, ExternalPlatformDtlInput, ALLOWED_PLATFORM_TYPES
from source_code.utils import domain_utils as date_utils


class ExternalPlatformCRUD(BaseCRUD[ExternalPlatformDtl]):
    def __init__(self):
        super().__init__(ExternalPlatformDtl)

    def list_all(self) -> List[ExternalPlatformDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT external_platform_id, name, platform_type, created_ts, last_updated_ts "
            "FROM external_platform_dtl ORDER BY external_platform_id"
        )
        return [ExternalPlatformDtl(**row) for row in rows]

    def _validate_type(self, t: str):
        if t not in ALLOWED_PLATFORM_TYPES:
            raise ValueError(f"platform_type must be one of {ALLOWED_PLATFORM_TYPES}")

    def save(self, item: ExternalPlatformDtlInput) -> ExternalPlatformDtl:
        self._validate_type(item.platform_type)
        next_id = date_utils.get_timestamp_with_microseconds()
        now = date_utils.get_current_date_time()
        platform = ExternalPlatformDtl(
            external_platform_id=next_id,
            name=item.name,
            platform_type=item.platform_type,
            created_ts=now,
            last_updated_ts=now,
        )
        sql = """
        INSERT INTO external_platform_dtl (
            external_platform_id, name, platform_type, created_ts, last_updated_ts
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (external_platform_id) DO UPDATE SET
            name = EXCLUDED.name,
            platform_type = EXCLUDED.platform_type,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (platform.external_platform_id, platform.name, platform.platform_type, platform.created_ts, platform.last_updated_ts)
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save external platform")
        return platform

    def get_security(self, pk: int) -> Optional[ExternalPlatformDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT external_platform_id, name, platform_type, created_ts, last_updated_ts "
            "FROM external_platform_dtl WHERE external_platform_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return ExternalPlatformDtl(**rows[0])

    def update(self, pk: int, item: ExternalPlatformDtlInput) -> ExternalPlatformDtl:
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("External platform not found")
        self._validate_type(item.platform_type)

        now = date_utils.get_current_date_time()
        sql = """
        UPDATE external_platform_dtl
        SET
            name = %s,
            platform_type = %s,
            last_updated_ts = %s
        WHERE external_platform_id = %s
        """
        params = (item.name, item.platform_type, now, pk)
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("External platform not found")
        return self.get_security(pk)

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM external_platform_dtl WHERE external_platform_id = %s",
            (pk,),
        )
        return affected > 0

    def save_many(self, items: List[ExternalPlatformDtlInput]) -> List[ExternalPlatformDtl]:
        results: List[ExternalPlatformDtl] = []
        for item in items:
            results.append(self.save(item))
        return results

# Keep a singleton instance for importers (routes)
external_platform_crud = ExternalPlatformCRUD()
