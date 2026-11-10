def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_customer(client, cid, name='Cliente'):
    r = client.post(f'/api/companies/{cid}/customers', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_stage(client, cid, name='Prospección', code='prospecting', order=1):
    r = client.post(f'/api/companies/{cid}/pipeline/stages', json={
        'name': name, 'code': code, 'order_index': order
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_opportunity(client, cid, customer_id, stage_id, name='Opp Test', amount=100.0):
    r = client.post(f'/api/companies/{cid}/pipeline/opportunities', json={
        'customer_id': customer_id, 'stage_id': stage_id,
        'name': name, 'amount': amount,
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_stage(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/pipeline/stages', json={
        'name': 'Propuesta', 'code': 'proposal', 'order_index': 3
    })
    assert r.status_code == 201
    assert r.get_json()['name'] == 'Propuesta'


def test_list_stages_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    _create_stage(client, c1, name='S1', code='s1')
    _create_stage(client, c2, name='S2', code='s2')
    
    r = client.get(f'/api/companies/{c1}/pipeline/stages')
    assert len(r.get_json()) == 1
    assert r.get_json()[0]['code'] == 's1'


def test_create_opportunity(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid)
    sid = _create_stage(client, cid)
    
    r = client.post(f'/api/companies/{cid}/pipeline/opportunities', json={
        'customer_id': cuid, 'stage_id': sid, 'name': 'Venta Grande', 'amount': 5000.0
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['name'] == 'Venta Grande'
    assert body['amount'] == 5000.0
    assert body['customer_name'] == 'Cliente'


def test_opportunity_tenant_isolation_relations(client):
    """Intenta crear una oportunidad en C1 usando un cliente de C2."""
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    cuid_c2 = _create_customer(client, c2)  # Cliente en C2
    sid_c1 = _create_stage(client, c1)      # Etapa en C1
    
    r = client.post(f'/api/companies/{c1}/pipeline/opportunities', json={
        'customer_id': cuid_c2, 'stage_id': sid_c1, 'name': 'Hack', 'amount': 10
    })
    assert r.status_code == 422
    assert 'no existe o no pertenece a esta empresa' in r.get_json()['message']


def test_patch_opportunity_stage(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid)
    sid1 = _create_stage(client, cid, name='S1', code='s1')
    sid2 = _create_stage(client, cid, name='S2', code='s2', order=2)
    oid = _create_opportunity(client, cid, cuid, sid1)
    
    r = client.patch(f'/api/companies/{cid}/pipeline/opportunities/{oid}', json={'stage_id': sid2})
    assert r.status_code == 200
    assert r.get_json()['stage_id'] == sid2
    assert r.get_json()['stage_name'] == 'S2'


def test_soft_delete_opportunity(client):
    cid = _create_company(client)
    cuid = _create_customer(client, cid)
    sid = _create_stage(client, cid)
    oid = _create_opportunity(client, cid, cuid, sid)
    
    r = client.delete(f'/api/companies/{cid}/pipeline/opportunities/{oid}')
    assert r.status_code == 204
    
    # Ya no aparece en el listado normal
    r = client.get(f'/api/companies/{cid}/pipeline/opportunities')
    assert r.get_json()['total'] == 0
    
    # Pero sí con include_inactive
    r = client.get(f'/api/companies/{cid}/pipeline/opportunities?include_inactive=1')
    assert r.get_json()['total'] == 1
    assert r.get_json()['items'][0]['is_active'] is False