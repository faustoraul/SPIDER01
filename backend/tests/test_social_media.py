import json

def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_account(client, cid, provider='facebook', ext_id='fb-001'):
    r = client.post(f'/api/companies/{cid}/social/accounts', json={
        'provider': provider,
        'external_account_id': ext_id,
        'access_token': 'fake-token'
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_social_account(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/social/accounts', json={
        'provider': 'whatsapp',
        'external_account_id': 'wa-test-123',
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['provider'] == 'whatsapp'
    assert 'access_token' not in body  # Seguridad: el token nunca se expone


def test_create_duplicate_account_conflict(client):
    cid = _create_company(client)
    _create_account(client, cid, 'facebook', 'fb-dup')
    r = client.post(f'/api/companies/{cid}/social/accounts', json={
        'provider': 'facebook',
        'external_account_id': 'fb-dup',
    })
    assert r.status_code == 409


def test_list_accounts_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    _create_account(client, c1, 'facebook', 'fb-c1')
    _create_account(client, c2, 'facebook', 'fb-c2')
    
    r = client.get(f'/api/companies/{c1}/social/accounts')
    assert len(r.get_json()) == 1
    assert r.get_json()[0]['external_account_id'] == 'fb-c1'


def test_webhook_creates_lead(client):
    cid = _create_company(client)
    payload = {
        'name': 'Test Lead Social',
        'email': 'social@test.local',
        'message': 'Quiero info'
    }
    r = client.post(f'/api/companies/{cid}/social/webhooks/facebook', json=payload)
    assert r.status_code == 201
    body = r.get_json()
    assert body['status'] == 'processed'
    assert body['lead_id'] is not None
    
    # Verificar que el lead existe
    r = client.get(f'/api/companies/{cid}/leads/{body["lead_id"]}')
    assert r.status_code == 200
    assert r.get_json()['source'] == 'facebook'
    assert r.get_json()['name'] == 'Test Lead Social'


def test_invalid_webhook_fails_but_is_saved(client):
    cid = _create_company(client)
    payload = {'email': 'sin-nombre@test.local'}  # Falta 'name'
    
    r = client.post(f'/api/companies/{cid}/social/webhooks/instagram', json=payload)
    assert r.status_code == 422
    body = r.get_json()
    assert body['status'] == 'failed'
    assert body['event_id'] is not None
    
    # Verificar que el evento fallido está en la base de datos
    r = client.get(f'/api/companies/{cid}/social/webhooks?status=failed')
    events = r.get_json()['items']
    assert len(events) == 1
    assert events[0]['provider'] == 'instagram'
    assert 'nombre de contacto válido' in events[0]['error_message']


def test_webhook_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    
    # Enviar webhook a C1
    client.post(f'/api/companies/{c1}/social/webhooks/facebook', json={'name': 'A'})
    
    # C2 no debe ver eventos de C1
    r = client.get(f'/api/companies/{c2}/social/webhooks')
    assert r.get_json()['total'] == 0


def test_unsupported_provider(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/social/webhooks/myspace', json={'name': 'A'})
    assert r.status_code == 422


def test_retry_failed_event(client):
    cid = _create_company(client)
    
    # 1. Crear un evento que fallará
    client.post(f'/api/companies/{cid}/social/webhooks/facebook', json={'email': 'bad@test.com'})
    r = client.get(f'/api/companies/{cid}/social/webhooks?status=failed')
    event_id = r.get_json()['items'][0]['id']
    
    # 2. Reintentar (sigue fallando porque el payload no tiene nombre)
    r = client.post(f'/api/companies/{cid}/social/webhooks/{event_id}/retry')
    assert r.status_code == 422