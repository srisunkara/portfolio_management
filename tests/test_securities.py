from fastapi.testclient import TestClient


def test_securities_crud_flow(client: TestClient):
    # Initially list
    r = client.get('/securities')
    assert r.status_code == 200
    initial = r.json()

    # Create
    payload = {
        "ticker": "XYZ",
        "name": "XYZ Corp",
        "company_name": "XYZ Corporation",
        "security_currency": "usd",
    }
    r = client.post('/securities/', json=payload)
    assert r.status_code == 200
    created = r.json()
    assert created['security_id']
    assert created['ticker'] == 'XYZ'
    assert created['security_currency'] == 'USD'

    sid = created['security_id']

    # Get by id
    r = client.get(f'/securities/{sid}')
    assert r.status_code == 200
    got = r.json()
    assert got['security_id'] == sid

    # Update (uses Input model per routes)
    update_payload = {
        "ticker": "XYZ",
        "name": "XYZ Corp Updated",
        "company_name": "XYZ Corporation",
        "security_currency": "EUR",
    }
    r = client.put(f'/securities/{sid}', json=update_payload)
    assert r.status_code == 200
    updated = r.json()
    assert updated['name'] == 'XYZ Corp Updated'
    assert updated['security_currency'] == 'EUR'

    # Export CSV
    r = client.get('/securities/export.csv')
    assert r.status_code == 200
    assert 'text/csv' in r.headers.get('content-type', '')

    # Delete
    r = client.delete(f'/securities/{sid}')
    assert r.status_code == 200
    assert r.json() == {"deleted": True}

    # Get missing -> 404
    r = client.get(f'/securities/{sid}')
    assert r.status_code == 404
