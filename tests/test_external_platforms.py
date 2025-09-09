from fastapi.testclient import TestClient


def test_external_platforms_validation_and_crud(client: TestClient):
    # invalid type
    r = client.post('/external-platforms/', json={"name": "Bad", "platform_type": "Invalid"})
    assert r.status_code == 400

    # valid create
    r = client.post('/external-platforms/', json={"name": "PricerA", "platform_type": "Pricing Platform"})
    assert r.status_code == 200
    item = r.json()
    eid = item['external_platform_id']
    assert item['name'] == 'PricerA'
    assert item['platform_type'] == 'Pricing Platform'

    # list
    r = client.get('/external-platforms')
    assert r.status_code == 200
    lst = r.json()
    assert any(x['external_platform_id'] == eid for x in lst)

    # update (full model expected on PUT)
    item['name'] = 'PricerA+'
    r = client.put(f'/external-platforms/{eid}', json=item)
    assert r.status_code == 200
    upd = r.json()
    assert upd['name'] == 'PricerA+'

    # export
    r = client.get('/external-platforms/export.csv')
    assert r.status_code == 200
    assert 'text/csv' in r.headers.get('content-type','')

    # delete
    r = client.delete(f'/external-platforms/{eid}')
    assert r.status_code == 200
    assert r.json() == {"deleted": True}
