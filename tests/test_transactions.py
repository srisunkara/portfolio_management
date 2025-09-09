from fastapi.testclient import TestClient
from datetime import date


def test_transactions_crud_and_full_view(client: TestClient, mock_db):
    # create a transaction (uses external_platform_id)
    payload = {
        "portfolio_id": 201,
        "security_id": 301,
        "external_platform_id": 401,
        "transaction_date": date.today().isoformat(),
        "transaction_type": "BUY",
        "transaction_qty": 10,
        "transaction_price": 5.5,
    }
    r = client.post('/transactions/', json=payload)
    assert r.status_code == 200
    txn = r.json()
    tid = txn['transaction_id']

    # list
    r = client.get('/transactions')
    assert r.status_code == 200
    assert any(x['transaction_id'] == tid for x in r.json())

    # prepare view rows for /transactions
    mock_db.view_v_transaction_full = [{
        'transaction_id': tid,
        'portfolio_id': 201,
        'portfolio_name': 'Core',
        'user_id': 101,
        'user_full_name': 'Jane Doe',
        'security_id': 301,
        'security_ticker': 'ABC',
        'security_name': 'ABC Inc',
        'external_platform_id': 401,
        'external_platform_name': 'BrokerX',
        'transaction_date': payload['transaction_date'],
        'transaction_type': 'BUY',
        'transaction_qty': 10.0,
        'transaction_price': 5.5,
        'transaction_fee': 0.0,
        'transaction_fee_percent': 0.0,
        'carry_fee': 0.0,
        'carry_fee_percent': 0.0,
        'management_fee': 0.0,
        'management_fee_percent': 0.0,
        'external_manager_fee': 0.0,
        'external_manager_fee_percent': 0.0,
        'gross_amount': 55.0,
        'total_fee': 0.0,
        'net_amount': 55.0,
        'created_ts': payload['transaction_date'],
        'last_updated_ts': payload['transaction_date'],
    }]

    r = client.get('/transactions')
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 1
    row = rows[0]
    assert row['external_platform_name'] == 'BrokerX'

    # update
    put_body = txn
    put_body['transaction_qty'] = 12
    r = client.put(f'/transactions/{tid}', json=put_body)
    assert r.status_code == 200
    assert r.json()['transaction_qty'] == 12

    # delete
    r = client.delete(f'/transactions/{tid}')
    assert r.status_code == 200
    assert r.json() == {"deleted": True}
