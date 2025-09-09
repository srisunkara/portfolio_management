from fastapi.testclient import TestClient


def test_users_create_hash_list_update_delete(client: TestClient):
    # create with password -> route hashes
    payload = {"first_name": "John", "last_name": "Smith", "email": "john@ex.com", "password": "secret"}
    r = client.post('/users/', json=payload)
    assert r.status_code == 200
    created = r.json()
    uid = created['user_id']
    assert created['first_name'] == 'John'

    # list
    r = client.get('/users')
    assert r.status_code == 200
    assert any(x['user_id'] == uid for x in r.json())

    # get
    r = client.get(f'/users/{uid}')
    assert r.status_code == 200

    # update (full model expected on PUT)
    created['last_name'] = 'S.'
    r = client.put(f'/users/{uid}', json=created)
    assert r.status_code == 200
    assert r.json()['last_name'] == 'S.'

    # export
    r = client.get('/users/export.csv')
    assert r.status_code == 200

    # delete
    r = client.delete(f'/users/{uid}')
    assert r.status_code == 200
    assert r.json() == {"deleted": True}
