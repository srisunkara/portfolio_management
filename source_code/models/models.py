# models.py
from datetime import datetime, timezone, date
from typing import Optional

from pydantic import BaseModel, Field


class UserDtl(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    is_admin: bool = False
    created_ts: Optional[datetime] = None
    last_updated_ts: Optional[datetime] = None


class UserDtlInput(BaseModel):
    first_name: str
    last_name: str
    email: str = None
    password: str = None
    # Do not allow clients to set admin via public APIs; default False
    is_admin: bool = False


class SecurityDtl(BaseModel):
    security_id: int
    ticker: str
    name: str
    company_name: str
    security_currency: str = 'USD'
    is_private: bool = False
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class SecurityDtlInput(BaseModel):
    ticker: str
    name: str
    company_name: str
    security_currency: str = 'USD'
    is_private: bool = False


class PortfolioDtl(BaseModel):
    portfolio_id: int
    user_id: int
    name: str
    open_date: date = Field(default_factory=date.today)
    close_date: Optional[date] = None
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class PortfolioDtlInput(BaseModel):
    user_id: int
    name: str
    open_date: date = Field(default_factory=date.today)
    close_date: Optional[date] = None


ALLOWED_PLATFORM_TYPES = ["Trading Platform", "Pricing Platform", "Secondary Trading Platform"]

# Common dictionary for transaction types: store codes, display labels
TRANSACTION_TYPES: dict[str, str] = {
    "B": "Buy",
    "S": "Sell",
}


class ExternalPlatformDtl(BaseModel):
    external_platform_id: int
    name: str
    platform_type: str
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class ExternalPlatformDtlInput(BaseModel):
    name: str
    platform_type: str


class TransactionDtl(BaseModel):
    transaction_id: int
    portfolio_id: int
    security_id: int
    external_platform_id: int
    transaction_date: date = Field(default_factory=date.today)
    transaction_type: str
    transaction_qty: float
    transaction_price: float
    #
    transaction_fee: float = 0.0
    transaction_fee_percent: float = 0.0
    carry_fee: float = 0.0
    carry_fee_percent: float = 0.0
    management_fee: float = 0.0
    management_fee_percent: float = 0.0
    external_manager_fee: float = 0.0
    external_manager_fee_percent: float = 0.0
    total_inv_amt: Optional[float] = 0.0
    rel_transaction_id: Optional[int] = None
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class TransactionDtlInput(BaseModel):
    portfolio_id: int
    security_id: int
    external_platform_id: int
    transaction_date: date = Field(default_factory=date.today)
    transaction_type: str
    transaction_qty: float
    transaction_price: float
    #
    transaction_fee: float = 0.0
    transaction_fee_percent: float = 0.0
    carry_fee: float = 0.0
    carry_fee_percent: float = 0.0
    management_fee: float = 0.0
    management_fee_percent: float = 0.0
    external_manager_fee: float = 0.0
    external_manager_fee_percent: float = 0.0
    total_inv_amt: Optional[float] = 0.0
    rel_transaction_id: Optional[int] = None


class HoldingDtl(BaseModel):
    holding_id: int
    holding_dt: date = date.today()
    portfolio_id: int
    security_id: int
    quantity: float
    price: float
    avg_price: float = 0.0
    market_value: float
    security_price_dt: Optional[date] = None
    # New computed fields
    holding_cost_amt: float = 0.0
    unreal_gain_loss_amt: float = 0.0
    unreal_gain_loss_perc: float = 0.0
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


# Add input model to mirror other modules
class HoldingDtlInput(BaseModel):
    holding_dt: date = date.today()
    portfolio_id: int
    security_id: int
    quantity: float
    price: float
    avg_price: float = 0.0
    market_value: float
    security_price_dt: Optional[date] = None
    # New computed fields (accepted for completeness; generally set by backend recalc)
    holding_cost_amt: float = 0.0
    unreal_gain_loss_amt: float = 0.0
    unreal_gain_loss_perc: float = 0.0


class SecurityPriceDtl(BaseModel):
    security_price_id: int
    security_id: int
    price_source_id: int
    price_date: date = date.today()
    price: float
    open_px: Optional[float] = None
    close_px: Optional[float] = None
    high_px: Optional[float] = None
    low_px: Optional[float] = None
    adj_close_px: Optional[float] = None
    volume: Optional[float] = None
    market_cap: float = 0.0
    addl_notes: Optional[str] = None
    price_currency: str = 'USD'
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class SecurityPriceDtlInput(BaseModel):
    security_id: int
    price_source_id: int
    price_date: date = date.today()
    price: float
    open_px: Optional[float] = None
    close_px: Optional[float] = None
    high_px: Optional[float] = None
    low_px: Optional[float] = None
    adj_close_px: Optional[float] = None
    volume: Optional[float] = None
    market_cap: float = 0.0
    addl_notes: Optional[str] = None
    price_currency: str = 'USD'
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class TransactionFullView(BaseModel):
    transaction_id: int
    portfolio_id: int
    portfolio_name: Optional[str] = None
    user_id: Optional[int] = None
    user_full_name: Optional[str] = None
    security_id: int
    security_ticker: Optional[str] = None
    security_name: Optional[str] = None
    external_platform_id: int
    external_platform_name: Optional[str] = None
    transaction_date: date
    transaction_type: str
    transaction_qty: float
    transaction_price: float
    transaction_fee: Optional[float] = 0.0
    transaction_fee_percent: Optional[float] = 0.0
    carry_fee: Optional[float] = 0.0
    carry_fee_percent: Optional[float] = 0.0
    management_fee: Optional[float] = 0.0
    management_fee_percent: Optional[float] = 0.0
    external_manager_fee: Optional[float] = 0.0
    external_manager_fee_percent: Optional[float] = 0.0
    gross_amount: Optional[float] = None
    total_fee: Optional[float] = None
    net_amount: Optional[float] = None
    total_inv_amt: Optional[float] = None
    rel_transaction_id: Optional[int] = None
    created_ts: datetime
    last_updated_ts: datetime


class TransactionByNameInput(BaseModel):
    portfolio_name: str
    security_ticker: str
    external_platform_name: str
    transaction_date: date = date.today()
    transaction_type: str
    transaction_qty: float
    transaction_price: float
    # Optional fees
    transaction_fee: float = 0.0
    transaction_fee_percent: float = 0.0
    carry_fee: float = 0.0
    carry_fee_percent: float = 0.0
    management_fee: float = 0.0
    management_fee_percent: float = 0.0
    external_manager_fee: float = 0.0
    external_manager_fee_percent: float = 0.0


class CompanyValuationDtl(BaseModel):
    company_valuation_id: int
    as_of_date: date = Field(default_factory=date.today)
    price_source: str = "External"
    company: Optional[str] = None
    sector_subsector: Optional[str] = None
    price: Optional[float] = None
    price_change_amt: Optional[float] = None
    price_change_perc: Optional[float] = None
    last_matched_price: Optional[str] = None
    share_class: Optional[str] = None
    post_money_valuation: Optional[str] = None
    price_per_share: Optional[float] = None
    amount_raised: Optional[str] = None
    raw_data_json: Optional[dict] = None
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class CompanyValuationDtlInput(BaseModel):
    as_of_date: date = Field(default_factory=date.today)
    price_source: str = "External"
    company: Optional[str] = None
    sector_subsector: Optional[str] = None
    price: Optional[float] = None
    price_change_amt: Optional[float] = None
    price_change_perc: Optional[float] = None
    last_matched_price: Optional[str] = None
    share_class: Optional[str] = None
    post_money_valuation: Optional[str] = None
    price_per_share: Optional[float] = None
    amount_raised: Optional[str] = None
    raw_data_json: Optional[dict] = None
