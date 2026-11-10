def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_lead(client, cid, **overrides):
    payload = {
        'name': overrides.pop('name', 'Lead Test'),
        'email': overrides.pop('email', 'lead@test.local'),
        'phone': overrides.pop('phone', '809-000-0000'),
        'source': overrides.pop('source', 'manual'),
        'status': overrides.pop('status', 'new'),
    }
    payload.update(overrides)
    r = client.post(f'/api/companies/{cid}/leads', json=payload)
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_lead(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/leads', json={
        'name': 'Carlos Gómez',
        'email': 'carlos@test.local',
        'source': 'facebook',
        'status': 'new',
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['name'] == 'Carlos Gómez'
    assert body['company_id'] == cid
    assert body['status'] == 'new'


def test_create_lead_invalid_status(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/leads', json={
        'name': 'X', 'status': 'super_hot',
    })
    assert r.status_code == 422


def test_list_leads_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    _create_lead(client, c1, name='A')
    _create_lead(client, c1, name='B')
    _create_lead(client, c2, name='C')

    r = client.get(f'/api/companies/{c1}/leads')
    assert r.status_code == 200
    body = r.get_json()
    assert body['total'] == 2
    assert all(item['company_id'] == c1 for item in body['items'])


def test_filter_leads_by_status(client):
    cid = _create_company(client)
    _create_lead(client, cid, name='A', status='new')
    _create_lead(client, cid, name='B', status='qualified')
    _create_lead(client, cid, name='C', status='qualified')

    r = client.get(f'/api/companies/{cid}/leads?status=qualified')
    assert r.status_code == 200
    assert r.get_json()['total'] == 2


def test_add_activity_and_get_detail(client):
    cid = _create_company(client)
    lid = _create_lead(client, cid)

    r = client.post(f'/api/companies/{cid}/leads/{lid}/activities', json={
        'activity_type': 'call',
        'notes': 'Llamada inicial',
        'created_by': 'vendedor@test.local',
    })
    assert r.status_code == 201
    assert r.get_json()['activity_type'] == 'call'

    r = client.get(f'/api/companies/{cid}/leads/{lid}')
    assert r.status_code == 200
    body = r.get_json()
    assert len(body['activities']) == 1
    assert body['activities'][0]['notes'] == 'Llamada inicial'


def test_convert_lead_to_customer(client):
    cid = _create_company(client)
    lid = _create_lead(client, cid, name='Roberto', email='roberto@test.local', status='qualified')

    r = client.post(f'/api/companies/{cid}/leads/{lid}/convert')
    assert r.status_code == 200
    body = r.get_json()
    
    assert body['lead']['status'] == 'converted'
    assert body['lead']['customer_id'] is not None
    assert body['customer']['name'] == 'Roberto'
    assert body['customer']['email'] == 'roberto@test.local'

    # Verificar que el cliente existe
    r = client.get(f'/api/companies/{cid}/customers/{body["customer"]["id"]}')
    assert r.status_code == 200


def test_convert_lead_twice_conflict(client):
    cid = _create_company(client)
    lid = _create_lead(client, cid, status='qualified')
    
    # Primera conversión
    r = client.post(f'/api/companies/{cid}/leads/{lid}/convert')
    assert r.status_code == 200

    # Segunda conversión debe fallar
    r = client.post(f'/api/companies/{cid}/leads/{lid}/convert')
    assert r.status_code == 409


def test_public_endpoint_forces_web_and_new(client):
    cid = _create_company(client)
    
    r = client.post(f'/api/public/companies/{cid}/leads', json={
        'name': 'Lead Público',
        'email': 'publico@test.local',
    })
    assert r.status_code == 201
    lid = r.get_json()['lead_id']

    r = client.get(f'/api/companies/{cid}/leads/{lid}')
    body = r.get_json()
    assert body['source'] == 'web'
    assert body['status'] == 'new'


def test_public_endpoint_ignores_injection(client):
    cid = _create_company(client)
    
    # Intentar inyectar status y source desde el endpoint público
    r = client.post(f'/api/public/companies/{cid}/leads', json={
        'name': 'Hack Attempt',
        'email': 'hack@test.local',
        'status': 'converted',
        'source': 'facebook',
    })
    assert r.status_code == 201
    lid = r.get_json()['lead_id']

    r = client.get(f'/api/companies/{cid}/leads/{lid}')
    body = r.get_json()
    assert body['source'] == 'web'       # ignoró 'facebook'
    assert body['status'] == 'new'       # ignoró 'converted'