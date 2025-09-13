# models.py
from datetime import datetime, timezone, date
from typing import Optional

from pydantic import BaseModel, Field


class UserDtl(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str = None
    password_hash: str = None
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class UserDtlInput(BaseModel):
    first_name: str
    last_name: str
    email: str = None
    password: str = None


class SecurityDtl(BaseModel):
    security_id: int
    ticker: str
    name: str
    company_name: str
    security_currency: str = 'USD'
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class SecurityDtlInput(BaseModel):
    ticker: str
    name: str
    company_name: str
    security_currency: str = 'USD'


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


class HoldingDtl(BaseModel):
    holding_id: int
    holding_dt: date = date.today()
    portfolio_id: int
    security_id: int
    quantity: float
    price: float
    market_value: float
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


# Add input model to mirror other modules
class HoldingDtlInput(BaseModel):
    holding_dt: date = date.today()
    portfolio_id: int
    security_id: int
    quantity: float
    price: float
    market_value: float


class SecurityPriceDtl(BaseModel):
    security_price_id: int
    security_id: int
    price_source: str
    price_date: date = date.today()
    price: float
    market_cap: float
    price_currency: str = 'USD'
    created_ts: datetime = datetime.now(timezone.utc)
    last_updated_ts: datetime = datetime.now(timezone.utc)


class SecurityPriceDtlInput(BaseModel):
    security_id: int
    price_source: str
    price_date: date = date.today()
    price: float
    market_cap: float
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
