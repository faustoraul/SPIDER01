from datetime import date

def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']

def _create_branch(client, cid, code='CENTRO'):
    r = client.post(f'/api/companies/{cid}/branches', json={'name': f'Suc {code}', 'code': code})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']

def _create_product(client, cid, sku='SKU-01', price=100.0):
    r = client.post(f'/api/companies/{cid}/products', json={'sku': sku, 'name': 'Prod', 'sale_price': price, 'tax_rate': 18})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']

def _stock_up(client, cid, bid, pid, qty=10):
    r = client.post(f'/api/companies/{cid}/inventory/movements', json={
        'branch_id': bid, 'product_id': pid, 'movement_type': 'in', 'quantity': qty
    })
    assert r.status_code == 201, r.get_json()

def _create_register(client, cid, bid):
    r = client.post(f'/api/companies/{cid}/cash-registers', json={'branch_id': bid, 'name': 'Caja 1'})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']

def _open_cash(client, cid, reg_id, amount=100.0):
    r = client.post(f'/api/companies/{cid}/cash-sessions', json={
        'cash_register_id': reg_id, 'user_name': 'Cajero', 'opening_amount': amount
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def test_create_sale_updates_stock_and_cash(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid, price=100.0)
    _stock_up(client, cid, bid, pid, 10)
    
    reg_id = _create_register(client, cid, bid)
    sess_id = _open_cash(client, cid, reg_id, 50.0)

    # Vender 2 productos a 100 + 18% = 236 total
    payload = {
        'branch_id': bid,
        'sale_number': 'F-001',
        'issue_date': date.today().isoformat(),
        'items': [{'product_id': pid, 'quantity': 2, 'unit_price': 100.0, 'tax_rate': 18.0, 'discount': 0.0}],
        'payments': [{'method': 'cash', 'amount': 236.0}]
    }
    r = client.post(f'/api/companies/{cid}/sales', json=payload)
    assert r.status_code == 201, r.get_json()
    assert r.get_json()['status'] == 'paid'
    assert r.get_json()['total'] == 236.0

    # 1. Verificar Stock (10 - 2 = 8)
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    assert r.get_json()[0]['quantity'] == 8.0

    # 2. Cerrar caja y verificar cuadre (50 apertura + 236 venta = 286)
    r = client.post(f'/api/companies/{cid}/cash-sessions/{sess_id}/close', json={'closing_amount': 286.0})
    assert r.status_code == 200
    assert r.get_json()['expected_amount'] == 286.0
    assert r.get_json()['difference'] == 0.0


def test_sale_insufficient_stock(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    _stock_up(client, cid, bid, pid, 1) # Solo hay 1
    
    reg_id = _create_register(client, cid, bid)
    _open_cash(client, cid, reg_id)

    payload = {
        'branch_id': bid,
        'sale_number': 'F-002',
        'issue_date': date.today().isoformat(),
        'items': [{'product_id': pid, 'quantity': 2, 'unit_price': 100.0, 'tax_rate': 0.0, 'discount': 0.0}],
        'payments': [{'method': 'cash', 'amount': 200.0}]
    }
    r = client.post(f'/api/companies/{cid}/sales', json=payload)
    assert r.status_code == 422
    assert 'Stock insuficiente' in r.get_json()['message']


def test_cash_payment_requires_open_session(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    _stock_up(client, cid, bid, pid, 10)
    
    # No abrimos caja
    payload = {
        'branch_id': bid,
        'sale_number': 'F-003',
        'issue_date': date.today().isoformat(),
        'items': [{'product_id': pid, 'quantity': 1, 'unit_price': 100.0, 'tax_rate': 0.0, 'discount': 0.0}],
        'payments': [{'method': 'cash', 'amount': 100.0}]
    }
    r = client.post(f'/api/companies/{cid}/sales', json=payload)
    assert r.status_code == 422
    assert 'sin un turno de caja abierto' in r.get_json()['message']