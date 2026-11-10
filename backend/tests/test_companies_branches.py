def _create_company(client, name='Acme', tax_id=None):
    payload = {'name': name}
    if tax_id:
        payload['tax_id'] = tax_id
    r = client.post('/api/companies', json=payload)
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_company(client):
    r = client.post('/api/companies', json={
        'name': 'Acme SRL', 'tax_id': '101-00001-1',
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['name'] == 'Acme SRL'
    assert body['id'] > 0


def test_create_company_missing_name(client):
    r = client.post('/api/companies', json={})
    assert r.status_code == 422


def test_create_company_non_json_body(client):
    r = client.post('/api/companies', data='not-json')
    assert r.status_code == 422


def test_duplicate_tax_id(client):
    payload = {'name': 'A', 'tax_id': 'XYZ'}
    r1 = client.post('/api/companies', json=payload)
    assert r1.status_code == 201
    r2 = client.post('/api/companies', json=payload)
    assert r2.status_code == 409


def test_create_branch(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/branches', json={
        'name': 'Sucursal Centro', 'code': 'CENTRO',
    })
    assert r.status_code == 201
    assert r.get_json()['company_id'] == cid


def test_create_branch_for_nonexistent_company(client):
    r = client.post('/api/companies/9999/branches', json={
        'name': 'X', 'code': 'X',
    })
    assert r.status_code == 404


def test_create_branch_missing_code(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/branches', json={'name': 'X'})
    assert r.status_code == 422


def test_branches_isolation(client):
    """Empresas distintas nunca comparten sucursales en las respuestas."""
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')

    client.post(f'/api/companies/{c1}/branches', json={'name': 'A', 'code': 'A'})
    client.post(f'/api/companies/{c1}/branches', json={'name': 'B', 'code': 'B'})
    client.post(f'/api/companies/{c2}/branches', json={'name': 'C', 'code': 'C'})

    r = client.get(f'/api/companies/{c1}/branches')
    assert r.status_code == 200
    branches = r.get_json()
    assert len(branches) == 2
    assert all(b['company_id'] == c1 for b in branches)

    r = client.get(f'/api/companies/{c2}/branches')
    assert r.status_code == 200
    assert len(r.get_json()) == 1
    assert r.get_json()[0]['company_id'] == c2


def test_duplicate_branch_code_within_company(client):
    cid = _create_company(client)
    client.post(f'/api/companies/{cid}/branches', json={'name': 'A', 'code': 'SAME'})
    r = client.post(f'/api/companies/{cid}/branches', json={'name': 'B', 'code': 'SAME'})
    assert r.status_code == 409


def test_same_code_allowed_in_different_companies(client):
    """El código de sucursal es único por empresa, no global."""
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    r1 = client.post(f'/api/companies/{c1}/branches', json={'name': 'A', 'code': 'SAME'})
    r2 = client.post(f'/api/companies/{c2}/branches', json={'name': 'B', 'code': 'SAME'})
    assert r1.status_code == 201
    assert r2.status_code == 201