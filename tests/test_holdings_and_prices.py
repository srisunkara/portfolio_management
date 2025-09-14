from fastapi.testclient import TestClient
from datetime import date


def test_holdings_crud(client: TestClient):
    payload = {
        "holding_dt": date.today().isoformat(),
        "portfolio_id": 201,
        "security_id": 301,
        "quantity": 100.0,
        "price": 12.5,
        "market_value": 1250.0,
    }
    r = client.post('/holdings/', json=payload)
    assert r.status_code == 200
    h = r.json()
    hid = h['holding_id']

    r = client.get('/holdings')
    assert r.status_code == 200

    r = client.get(f'/holdings/{hid}')
    assert r.status_code == 200

    h['price'] = 13.0
    r = client.put(f'/holdings/{hid}', json=h)
    assert r.status_code == 200
    assert r.json()['price'] == 13.0

    r = client.get('/holdings/export.csv')
    assert r.status_code == 200

    r = client.delete(f'/holdings/{hid}')
    assert r.status_code == 200


def test_security_prices_crud(client: TestClient):
    payload = {
        "security_id": 301,
        "price_source_id": 401,
        "price_date": date.today().isoformat(),
        "price": 99.5,
        "market_cap": 1_000_000.0,
        "price_currency": "USD"
    }
    r = client.post('/security-prices/', json=payload)
    assert r.status_code == 200
    p = r.json()
    pid = p['security_price_id']

    r = client.get('/security-prices')
    assert r.status_code == 200

    r = client.get(f'/security-prices/{pid}')
    assert r.status_code == 200

    p['price'] = 101.25
    r = client.put(f'/security-prices/{pid}', json=p)
    assert r.status_code == 200
    assert r.json()['price'] == 101.25

    r = client.get('/security-prices/export.csv')
    assert r.status_code == 200

    r = client.delete(f'/security-prices/{pid}')
    assert r.status_code == 200
