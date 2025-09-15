import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import routers
from source_code.crud.security_api_routes import router as securities_router
from source_code.crud.portfolio_api_routes import router as portfolios_router
from source_code.crud.user_api_routes import router as users_router
from source_code.crud.holding_api_routes import router as holdings_router
from source_code.crud.security_price_api_routes import router as security_prices_router
from source_code.crud.transaction_api_routes import router as transactions_router
from source_code.crud.external_platform_api_routes import router as external_platforms_router

# We'll monkeypatch pg_db_conn_manager used by CRUD layers
from source_code.config import pg_db_conn_manager


class MockDB:
    def __init__(self):
        # simple in-memory stores keyed by id
        self.tables = {
            'security_dtl': {},
            'portfolio_dtl': {},
            'user_dtl': {},
            'holding_dtl': {},
            'security_price_dtl': {},
            'transaction_dtl': {},
            'external_platform_dtl': {},
        }
        self.view_v_transaction_full = []

    def fetch_data(self, sql: str, params: tuple | None = None):  # naive parser based on FROM ... WHERE pk
        sql_low = sql.lower()
        if 'from security_dtl' in sql_low:
            return self._fetch_generic('security_dtl', sql_low, params)
        if 'from portfolio_dtl' in sql_low:
            return self._fetch_generic('portfolio_dtl', sql_low, params)
        if 'from user_dtl' in sql_low:
            return self._fetch_generic('user_dtl', sql_low, params)
        if 'from holding_dtl' in sql_low:
            return self._fetch_generic('holding_dtl', sql_low, params)
        if 'from security_price_dtl' in sql_low:
            return self._fetch_generic('security_price_dtl', sql_low, params)
        if 'from transaction_dtl' in sql_low:
            return self._fetch_generic('transaction_dtl', sql_low, params)
        if 'from v_transaction_full' in sql_low:
            # return the preset view rows
            return list(self.view_v_transaction_full)
        return []

    def _fetch_generic(self, table, sql_low, params):
        store = self.tables[table]
        if 'where' in sql_low and ' = %s' in sql_low:
            # assume WHERE <pk> = %s
            pk = params[0] if params else None
            row = store.get(pk)
            return [row] if row else []
        return list(store.values())

    def execute_query(self, sql: str, params: tuple | None = None) -> int:
        sql_low = sql.lower()
        # handle inserts/updates/deletes per table heuristically
        if 'insert into security_dtl' in sql_low:
            security_id, ticker, name, company_name, currency, created_ts, last_updated_ts = params
            self.tables['security_dtl'][security_id] = {
                'security_id': security_id,
                'ticker': ticker,
                'name': name,
                'company_name': company_name,
                'security_currency': currency,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('delete from security_dtl'):
            pk = params[0]
            return 1 if self.tables['security_dtl'].pop(pk, None) is not None else 0

        if 'insert into portfolio_dtl' in sql_low:
            (portfolio_id, user_id, name, open_date, close_date, created_ts, last_updated_ts) = params
            self.tables['portfolio_dtl'][portfolio_id] = {
                'portfolio_id': portfolio_id,
                'user_id': user_id,
                'name': name,
                'open_date': open_date,
                'close_date': close_date,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update portfolio_dtl'):
            user_id, name, open_date, close_date, last_updated_ts, pk = params
            row = self.tables['portfolio_dtl'].get(pk)
            if not row:
                return 0
            row.update({'user_id': user_id, 'name': name, 'open_date': open_date, 'close_date': close_date, 'last_updated_ts': last_updated_ts})
            return 1
        if sql_low.startswith('delete from portfolio_dtl'):
            pk = params[0]
            return 1 if self.tables['portfolio_dtl'].pop(pk, None) is not None else 0

        if 'insert into user_dtl' in sql_low:
            # dynamic columns handling already done by CRUD; we only store resulting params tuple order
            # Extract in order: columns can vary; use indices by detecting email/password_hash presence length
            # But we cannot infer names here; tests will verify via list queries using SELECT fixed columns
            # We'll reconstruct based on length
            values = list(params)
            # Try to read by positions: last two are created_ts, last_updated_ts; first is user_id; then names and optional email/password_hash
            user_id = values[0]
            first_name = values[1]
            last_name = values[2]
            # find created_ts & last_updated_ts at end
            created_ts = values[-2]
            last_updated_ts = values[-1]
            email = None
            password_hash = None
            # find possible email/password_hash among middle values
            middle = values[3:-2]
            for v in middle:
                # simplistic guess: if contains '@' treat as email; else treat as password_hash
                if isinstance(v, str) and '@' in v and email is None:
                    email = v
                else:
                    password_hash = v
            self.tables['user_dtl'][user_id] = {
                'user_id': user_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password_hash': password_hash,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update user_dtl'):
            first_name, last_name, email, password_hash, last_updated_ts, pk = params
            row = self.tables['user_dtl'].get(pk)
            if not row:
                return 0
            row.update({'first_name': first_name, 'last_name': last_name, 'email': email, 'password_hash': password_hash, 'last_updated_ts': last_updated_ts})
            return 1
        if sql_low.startswith('delete from user_dtl'):
            pk = params[0]
            return 1 if self.tables['user_dtl'].pop(pk, None) is not None else 0

        if 'insert into external_platform_dtl' in sql_low:
            external_platform_id, name, platform_type, created_ts, last_updated_ts = params
            self.tables['external_platform_dtl'][external_platform_id] = {
                'external_platform_id': external_platform_id,
                'name': name,
                'platform_type': platform_type,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update external_platform_dtl'):
            name, platform_type, last_updated_ts, pk = params
            row = self.tables['external_platform_dtl'].get(pk)
            if not row:
                return 0
            row.update({'name': name, 'platform_type': platform_type, 'last_updated_ts': last_updated_ts})
            return 1
        if sql_low.startswith('delete from external_platform_dtl'):
            pk = params[0]
            return 1 if self.tables['external_platform_dtl'].pop(pk, None) is not None else 0

        if 'insert into holding_dtl' in sql_low:
            (holding_id, holding_dt, portfolio_id, security_id, quantity, price, market_value, created_ts, last_updated_ts) = params
            self.tables['holding_dtl'][holding_id] = {
                'holding_id': holding_id,
                'holding_dt': holding_dt,
                'portfolio_id': portfolio_id,
                'security_id': security_id,
                'quantity': quantity,
                'price': price,
                'market_value': market_value,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update holding_dtl'):
            (holding_dt, portfolio_id, security_id, quantity, price, market_value, last_updated_ts, pk) = params
            row = self.tables['holding_dtl'].get(pk)
            if not row:
                return 0
            row.update({'holding_dt': holding_dt, 'portfolio_id': portfolio_id, 'security_id': security_id, 'quantity': quantity, 'price': price, 'market_value': market_value, 'last_updated_ts': last_updated_ts})
            return 1
        if sql_low.startswith('delete from holding_dtl'):
            pk = params[0]
            return 1 if self.tables['holding_dtl'].pop(pk, None) is not None else 0

        if 'insert into security_price_dtl' in sql_low:
            (security_price_id, security_id, price_source_id, price_date, price, market_cap, addl_notes, price_currency, created_ts, last_updated_ts) = params
            self.tables['security_price_dtl'][security_price_id] = {
                'security_price_id': security_price_id,
                'security_id': security_id,
                'price_source_id': price_source_id,
                'price_date': price_date,
                'price': price,
                'market_cap': market_cap,
                'addl_notes': addl_notes,
                'price_currency': price_currency,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update security_price_dtl'):
            (security_id, price_source_id, price_date, price, market_cap, addl_notes, price_currency, last_updated_ts, pk) = params
            row = self.tables['security_price_dtl'].get(pk)
            if not row:
                return 0
            row.update({'security_id': security_id, 'price_source_id': price_source_id, 'price_date': price_date, 'price': price, 'market_cap': market_cap, 'addl_notes': addl_notes, 'price_currency': price_currency, 'last_updated_ts': last_updated_ts})
            return 1
        if sql_low.startswith('delete from security_price_dtl'):
            pk = params[0]
            return 1 if self.tables['security_price_dtl'].pop(pk, None) is not None else 0

        if 'insert into transaction_dtl' in sql_low:
            (transaction_id, portfolio_id, security_id, external_platform_id, transaction_date, transaction_type,
             transaction_qty, transaction_price, transaction_fee, transaction_fee_percent,
             carry_fee, carry_fee_percent, management_fee, management_fee_percent,
             external_manager_fee, external_manager_fee_percent, total_inv_amt, created_ts, last_updated_ts) = params
            self.tables['transaction_dtl'][transaction_id] = {
                'transaction_id': transaction_id,
                'portfolio_id': portfolio_id,
                'security_id': security_id,
                'external_platform_id': external_platform_id,
                'transaction_date': transaction_date,
                'transaction_type': transaction_type,
                'transaction_qty': transaction_qty,
                'transaction_price': transaction_price,
                'transaction_fee': transaction_fee,
                'transaction_fee_percent': transaction_fee_percent,
                'carry_fee': carry_fee,
                'carry_fee_percent': carry_fee_percent,
                'management_fee': management_fee,
                'management_fee_percent': management_fee_percent,
                'external_manager_fee': external_manager_fee,
                'external_manager_fee_percent': external_manager_fee_percent,
                'total_inv_amt': total_inv_amt,
                'created_ts': created_ts,
                'last_updated_ts': last_updated_ts,
            }
            return 1
        if sql_low.startswith('update transaction_dtl'):
            (portfolio_id, security_id, external_platform_id, transaction_date, transaction_type, transaction_qty, transaction_price,
             transaction_fee, transaction_fee_percent, carry_fee, carry_fee_percent, management_fee, management_fee_percent,
             external_manager_fee, external_manager_fee_percent, total_inv_amt, last_updated_ts, pk) = params
            row = self.tables['transaction_dtl'].get(pk)
            if not row:
                return 0
            row.update({
                'portfolio_id': portfolio_id,
                'security_id': security_id,
                'external_platform_id': external_platform_id,
                'transaction_date': transaction_date,
                'transaction_type': transaction_type,
                'transaction_qty': transaction_qty,
                'transaction_price': transaction_price,
                'transaction_fee': transaction_fee,
                'transaction_fee_percent': transaction_fee_percent,
                'carry_fee': carry_fee,
                'carry_fee_percent': carry_fee_percent,
                'management_fee': management_fee,
                'management_fee_percent': management_fee_percent,
                'external_manager_fee': external_manager_fee,
                'external_manager_fee_percent': external_manager_fee_percent,
                'total_inv_amt': total_inv_amt,
                'last_updated_ts': last_updated_ts,
            })
            return 1
        if sql_low.startswith('delete from transaction_dtl'):
            pk = params[0]
            return 1 if self.tables['transaction_dtl'].pop(pk, None) is not None else 0

        return 0


@pytest.fixture(scope="session")
def app():
    app = FastAPI()
    app.include_router(securities_router)
    app.include_router(portfolios_router)
    app.include_router(users_router)
    app.include_router(holdings_router)
    app.include_router(security_prices_router)
    app.include_router(transactions_router)
    app.include_router(external_platforms_router)
    return app


@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    mock = MockDB()

    # Pre-load some reference rows for tests
    # Users
    mock.tables['user_dtl'][101] = {
        'user_id': 101, 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@example.com',
        'password_hash': None, 'created_ts': None, 'last_updated_ts': None
    }
    # Portfolios
    mock.tables['portfolio_dtl'][201] = {
        'portfolio_id': 201, 'user_id': 101, 'name': 'Core', 'open_date': None, 'close_date': None,
        'created_ts': None, 'last_updated_ts': None
    }
    # Securities
    mock.tables['security_dtl'][301] = {
        'security_id': 301, 'ticker': 'ABC', 'name': 'ABC Inc', 'company_name': 'ABC Inc', 'security_currency': 'USD',
        'created_ts': None, 'last_updated_ts': None
    }
    # External Platforms
    mock.tables['external_platform_dtl'][401] = {
        'external_platform_id': 401, 'name': 'BrokerX', 'platform_type': 'Trading Platform', 'created_ts': None, 'last_updated_ts': None
    }

    # Monkeypatch functions
    monkeypatch.setattr(pg_db_conn_manager, 'fetch_data', mock.fetch_data)
    monkeypatch.setattr(pg_db_conn_manager, 'execute_query', mock.execute_query)

    # Expose mock for tests that need to inject view rows
    yield mock


@pytest.fixture()
def client(app):
    return TestClient(app)
