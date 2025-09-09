from fastapi.testclient import TestClient
from datetime import date


def test_portfolios_create_update_list_delete(client: TestClient):
    # Create with open_date defaulted in backend if omitted; but we provide explicit
    payload = {
        "user_id": 101,
        "name": "Growth",
        "open_date": date.today().isoformat(),
    }
    r = client.post('/portfolios/', json=payload)
    assert r.status_code == 200
    pf = r.json()
    pid = pf['portfolio_id']

    # list
    r = client.get('/portfolios')
    assert r.status_code == 200
    assert any(x['portfolio_id'] == pid for x in r.json())

    # get
    r = client.get(f'/portfolios/{pid}')
    assert r.status_code == 200

    # update using Input model (route expects PortfolioDtlInput)
    r = client.put(f'/portfolios/{pid}', json={"user_id": 101, "name": "Growth+", "open_date": payload['open_date'], "close_date": None})
    assert r.status_code == 200
    assert r.json()['name'] == 'Growth+'

    # export
    r = client.get('/portfolios/export.csv')
    assert r.status_code == 200
    assert 'text/csv' in r.headers.get('content-type','')

    # delete
    r = client.delete(f'/portfolios/{pid}')
    assert r.status_code == 200
    assert r.json() == {"deleted": True}
