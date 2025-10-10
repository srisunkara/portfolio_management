# source_code/crud/company_valuations_crud_operations.py
from typing import List, Optional
from datetime import date

from source_code.config import pg_db_conn_manager
from source_code.crud.base import BaseCRUD
from source_code.models.models import CompanyValuationDtl, CompanyValuationDtlInput
from source_code.utils import domain_utils as date_utils


class CompanyValuationCRUD(BaseCRUD[CompanyValuationDtl]):
    def __init__(self):
        super().__init__(CompanyValuationDtl)

    def list_all(self) -> List[CompanyValuationDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT company_valuation_id, as_of_date, price_source, company, sector_subsector, "
            "price, price_change_amt, price_change_perc, last_matched_price, "
            "share_class, post_money_valuation, price_per_share, amount_raised, raw_data_json, "
            "created_ts, last_updated_ts "
            "FROM public.company_valuations ORDER BY as_of_date DESC, company"
        )
        return [CompanyValuationDtl(**row) for row in rows]

    def list_by_date(self, target_date: date) -> List[CompanyValuationDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT company_valuation_id, as_of_date, price_source, company, sector_subsector, "
            "price, price_change_amt, price_change_perc, last_matched_price, "
            "share_class, post_money_valuation, price_per_share, amount_raised, raw_data_json, "
            "created_ts, last_updated_ts "
            "FROM public.company_valuations WHERE as_of_date = %s ORDER BY company",
            (target_date,)
        )
        return [CompanyValuationDtl(**row) for row in rows]

    def save(self, item: CompanyValuationDtlInput) -> CompanyValuationDtl:
        # Check if a record already exists for the same company/date/source
        existing_rows = pg_db_conn_manager.fetch_data(
            "SELECT company_valuation_id FROM public.company_valuations "
            "WHERE company = %s AND as_of_date = %s AND price_source = %s LIMIT 1",
            (item.company, item.as_of_date, item.price_source),
        )
        
        now = date_utils.get_current_date_time()
        if existing_rows:
            # Update existing record
            existing_id = existing_rows[0]["company_valuation_id"]
            update_sql = (
                "UPDATE public.company_valuations\n"
                "SET price = %s,\n"
                "    price_change_amt = %s,\n"
                "    price_change_perc = %s,\n"
                "    last_matched_price = %s,\n"
                "    share_class = %s,\n"
                "    post_money_valuation = %s,\n"
                "    price_per_share = %s,\n"
                "    amount_raised = %s,\n"
                "    raw_data_json = %s,\n"
                "    last_updated_ts = %s\n"
                "WHERE company_valuation_id = %s"
            )
            params = (
                item.price, item.price_change_amt, item.price_change_perc,
                item.last_matched_price, item.share_class, item.post_money_valuation,
                item.price_per_share, item.amount_raised, item.raw_data_json,
                now, existing_id,
            )
            affected = pg_db_conn_manager.execute_query(update_sql, params)
            if affected == 0:
                raise RuntimeError("Failed to update company valuation")
            return self.get_security(existing_id)
        
        # Create new record
        next_id = date_utils.get_timestamp_with_microseconds()
        company = CompanyValuationDtl(
            company_valuation_id=next_id,
            as_of_date=item.as_of_date,
            price_source=item.price_source,
            company=item.company,
            sector_subsector=item.sector_subsector,
            price=item.price,
            price_change_amt=item.price_change_amt,
            price_change_perc=item.price_change_perc,
            last_matched_price=item.last_matched_price,
            share_class=item.share_class,
            post_money_valuation=item.post_money_valuation,
            price_per_share=item.price_per_share,
            amount_raised=item.amount_raised,
            raw_data_json=item.raw_data_json,
            created_ts=now,
            last_updated_ts=now,
        )
        
        insert_sql = """
        INSERT INTO public.company_valuations (
            company_valuation_id, as_of_date, price_source, company, sector_subsector,
            price, price_change_amt, price_change_perc, last_matched_price,
            share_class, post_money_valuation, price_per_share, amount_raised,
            raw_data_json, created_ts, last_updated_ts
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (company_valuation_id) DO UPDATE SET
            as_of_date = EXCLUDED.as_of_date,
            price_source = EXCLUDED.price_source,
            company = EXCLUDED.company,
            sector_subsector = EXCLUDED.sector_subsector,
            price = EXCLUDED.price,
            price_change_amt = EXCLUDED.price_change_amt,
            price_change_perc = EXCLUDED.price_change_perc,
            last_matched_price = EXCLUDED.last_matched_price,
            share_class = EXCLUDED.share_class,
            post_money_valuation = EXCLUDED.post_money_valuation,
            price_per_share = EXCLUDED.price_per_share,
            amount_raised = EXCLUDED.amount_raised,
            raw_data_json = EXCLUDED.raw_data_json,
            last_updated_ts = EXCLUDED.last_updated_ts
        """
        params = (
            company.company_valuation_id, company.as_of_date, company.price_source,
            company.company, company.sector_subsector, company.price,
            company.price_change_amt, company.price_change_perc, company.last_matched_price,
            company.share_class, company.post_money_valuation, company.price_per_share,
            company.amount_raised, company.raw_data_json, company.created_ts, company.last_updated_ts
        )
        affected = pg_db_conn_manager.execute_query(insert_sql, params)
        if affected == 0:
            raise RuntimeError("Failed to save company valuation")
        return company

    def save_many(self, items: List[CompanyValuationDtlInput]) -> List[CompanyValuationDtl]:
        result: List[CompanyValuationDtl] = []
        for item in items:
            result.append(self.save(item))
        return result

    def get_security(self, pk: int) -> Optional[CompanyValuationDtl]:
        rows = pg_db_conn_manager.fetch_data(
            "SELECT company_valuation_id, as_of_date, price_source, company, sector_subsector, "
            "price, price_change_amt, price_change_perc, last_matched_price, "
            "share_class, post_money_valuation, price_per_share, amount_raised, raw_data_json, "
            "created_ts, last_updated_ts "
            "FROM public.company_valuations WHERE company_valuation_id = %s",
            (pk,),
        )
        if not rows:
            return None
        return CompanyValuationDtl(**rows[0])

    def update(self, pk: int, item: CompanyValuationDtlInput) -> CompanyValuationDtl:
        # Ensure exists
        existing = self.get_security(pk)
        if not existing:
            raise KeyError("Company valuation not found")

        sql = """
        UPDATE public.company_valuations
        SET
            as_of_date = %s,
            price_source = %s,
            company = %s,
            sector_subsector = %s,
            price = %s,
            price_change_amt = %s,
            price_change_perc = %s,
            last_matched_price = %s,
            share_class = %s,
            post_money_valuation = %s,
            price_per_share = %s,
            amount_raised = %s,
            raw_data_json = %s,
            last_updated_ts = %s
        WHERE company_valuation_id = %s
        """
        params = (
            item.as_of_date, item.price_source, item.company, item.sector_subsector,
            item.price, item.price_change_amt, item.price_change_perc,
            item.last_matched_price, item.share_class, item.post_money_valuation,
            item.price_per_share, item.amount_raised, item.raw_data_json,
            date_utils.get_current_date_time(), pk,
        )
        affected = pg_db_conn_manager.execute_query(sql, params)
        if affected == 0:
            raise KeyError("Company valuation not found")
        return self.get_security(pk)

    def delete(self, pk: int) -> bool:
        affected = pg_db_conn_manager.execute_query(
            "DELETE FROM public.company_valuations WHERE company_valuation_id = %s",
            (pk,),
        )
        return affected > 0


# Keep a singleton instance for importers (routes)
company_valuation_crud = CompanyValuationCRUD()