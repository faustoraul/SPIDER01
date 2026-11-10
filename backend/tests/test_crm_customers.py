def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_customer(client, cid, **overrides):
    payload = {
        'name': overrides.pop('name', 'Cliente X'),
        'customer_type': overrides.pop('customer_type', 'individual'),
        'identification': overrides.pop('identification', None),
        'email': overrides.pop('email', None),
    }
    payload.update(overrides)
    r = client.post(f'/api/companies/{cid}/customers', json=payload)
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_customer(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/customers', json={
        'name': 'Juan Pérez',
        'customer_type': 'individual',
        'email': 'juan@test.local',
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['name'] == 'Juan Pérez'
    assert body['company_id'] == cid
    assert body['is_active'] is True


def test_create_customer_missing_name(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/customers', json={'customer_type': 'individual'})
    assert r.status_code == 422


def test_create_customer_invalid_type(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/customers', json={
        'name': 'X', 'customer_type': 'alien',
    })
    assert r.status_code == 422


def test_list_customers_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    _create_customer(client, c1, name='A')
    _create_customer(client, c1, name='B')
    _create_customer(client, c2, name='C')

    r = client.get(f'/api/companies/{c1}/customers')
    assert r.status_code == 200
    body = r.get_json()
    assert body['total'] == 2
    assert all(item['company_id'] == c1 for item in body['items'])


def test_duplicate_identification_within_company(client):
    cid = _create_company(client)
    _create_customer(client, cid, name='A', identification='123')
    r = client.post(f'/api/companies/{cid}/customers', json={
        'name': 'B', 'customer_type': 'individual', 'identification': '123',
    })
    assert r.status_code == 409


def test_same_identification_allowed_in_different_companies(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    r1 = client.post(f'/api/companies/{c1}/customers', json={
        'name': 'A', 'customer_type': 'individual', 'identification': 'SAME',
    })
    r2 = client.post(f'/api/companies/{c2}/customers', json={
        'name': 'B', 'customer_type': 'individual', 'identification': 'SAME',
    })
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_get_customer_detail_with_contacts(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='Cliente')

    client.post(f'/api/companies/{cid}/customers/{cuid}/contacts', json={
        'first_name': 'Pedro', 'last_name': 'R', 'is_primary': True,
    })
    client.post(f'/api/companies/{cid}/customers/{cuid}/contacts', json={
        'first_name': 'Ana', 'last_name': 'T',
    })

    r = client.get(f'/api/companies/{cid}/customers/{cuid}')
    assert r.status_code == 200
    body = r.get_json()
    assert len(body['contacts']) == 2
    primary = [c for c in body['contacts'] if c['is_primary']]
    assert len(primary) == 1
    assert primary[0]['first_name'] == 'Pedro'


def test_update_customer_put(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='Original')

    r = client.put(f'/api/companies/{cid}/customers/{cuid}', json={
        'name': 'Actualizado',
        'customer_type': 'company',
        'email': 'a@b.test',
        'phone': None,
        'identification': None,
        'address': None,
        'notes': None,
    })
    assert r.status_code == 200
    body = r.get_json()
    assert body['name'] == 'Actualizado'
    assert body['customer_type'] == 'company'
    assert body['email'] == 'a@b.test'


def test_patch_customer(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='Original', email='x@y.test')

    r = client.patch(f'/api/companies/{cid}/customers/{cuid}', json={'phone': '809-555-0000'})
    assert r.status_code == 200
    body = r.get_json()
    assert body['phone'] == '809-555-0000'
    assert body['name'] == 'Original'
    assert body['email'] == 'x@y.test'


def test_soft_delete_customer(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='Temporal')

    r = client.delete(f'/api/companies/{cid}/customers/{cuid}')
    assert r.status_code == 204

    r = client.get(f'/api/companies/{cid}/customers')
    assert r.get_json()['total'] == 0

    r = client.get(f'/api/companies/{cid}/customers/{cuid}')
    assert r.status_code == 404

    r = client.get(f'/api/companies/{cid}/customers?include_inactive=1')
    assert r.get_json()['total'] == 1
    assert r.get_json()['items'][0]['is_active'] is False


def test_only_one_primary_contact_per_customer(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='C')

    r1 = client.post(f'/api/companies/{cid}/customers/{cuid}/contacts', json={
        'first_name': 'Primero', 'is_primary': True,
    })
    r2 = client.post(f'/api/companies/{cid}/customers/{cuid}/contacts', json={
        'first_name': 'Segundo', 'is_primary': True,
    })
    assert r1.status_code == 201
    assert r2.status_code == 201

    r = client.get(f'/api/companies/{cid}/customers/{cuid}')
    contacts = r.get_json()['contacts']
    primaries = [c for c in contacts if c['is_primary']]
    assert len(primaries) == 1
    assert primaries[0]['first_name'] == 'Segundo'


def test_delete_contact(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid, name='C')
    r = client.post(f'/api/companies/{cid}/customers/{cuid}/contacts', json={'first_name': 'X'})
    contact_id = r.get_json()['id']

    r = client.delete(f'/api/companies/{cid}/customers/{cuid}/contacts/{contact_id}')
    assert r.status_code == 204

    r = client.get(f'/api/companies/{cid}/customers/{cuid}')
    assert r.get_json()['contacts'] == []


def test_customer_from_other_company_404(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    cuid = _create_customer(client, c1, name='De C1')

    r = client.get(f'/api/companies/{c2}/customers/{cuid}')
    assert r.status_code == 404