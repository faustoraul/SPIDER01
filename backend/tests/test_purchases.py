from datetime import date

def _create_company(client, name='Acme'):
    r = client.post('/api/companies', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_branch(client, cid, code='CENTRO'):
    r = client.post(f'/api/companies/{cid}/branches', json={
        'name': f'Sucursal {code}', 'code': code,
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_product(client, cid, sku='SKU-001', name='Producto X'):
    r = client.post(f'/api/companies/{cid}/products', json={
        'sku': sku, 'name': name, 'cost_price': 10, 'sale_price': 20
    })
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_supplier(client, cid, name='Prov X'):
    r = client.post(f'/api/companies/{cid}/suppliers', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_order(client, cid, sup_id, branch_id, product_id, order_number='PO-1'):
    payload = {
        'supplier_id': sup_id,
        'branch_id': branch_id,
        'order_number': order_number,
        'order_date': date.today().isoformat(),
        'items': [
            {'product_id': product_id, 'quantity': 10, 'unit_cost': 5.0}
        ]
    }
    r = client.post(f'/api/companies/{cid}/purchase-orders', json=payload)
    return r


# ---------- Proveedores ----------

def test_create_supplier(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/suppliers', json={'name': 'Nuevo Prov'})
    assert r.status_code == 201
    assert r.get_json()['name'] == 'Nuevo Prov'


def test_duplicate_supplier_conflict(client):
    cid = _create_company(client)
    _create_supplier(client, cid, 'Dup')
    r = client.post(f'/api/companies/{cid}/suppliers', json={'name': 'Dup'})
    assert r.status_code == 409


# ---------- Órdenes de Compra ----------

def test_create_order_calculates_total(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    sid = _create_supplier(client, cid)
    
    r = _create_order(client, cid, sid, bid, pid)
    assert r.status_code == 201
    body = r.get_json()
    assert body['total'] == 50.0  # 10 * 5.0
    assert body['status'] == 'draft'
    assert len(body['items']) == 1


def test_order_invalid_supplier_other_company(client):
    c1 = _create_company(client, 'C1')
    c2 = _create_company(client, 'C2')
    bid = _create_branch(client, c1)
    pid = _create_product(client, c1)
    sid_c2 = _create_supplier(client, c2)
    
    r = _create_order(client, c1, sid_c2, bid, pid)
    assert r.status_code == 422


def test_receive_order_updates_inventory(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    sid = _create_supplier(client, cid)
    
    r = _create_order(client, cid, sid, bid, pid)
    order_id = r.get_json()['id']
    
    # Recibir orden
    r = client.post(f'/api/companies/{cid}/purchase-orders/{order_id}/receive')
    assert r.status_code == 200
    assert r.get_json()['status'] == 'received'
    
    # Verificar inventario
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    stock = r.get_json()
    assert len(stock) == 1
    assert stock[0]['quantity'] == 10.0


def test_receive_order_twice_conflict(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    sid = _create_supplier(client, cid)
    order_id = _create_order(client, cid, sid, bid, pid).get_json()['id']
    
    client.post(f'/api/companies/{cid}/purchase-orders/{order_id}/receive')
    r = client.post(f'/api/companies/{cid}/purchase-orders/{order_id}/receive')
    assert r.status_code == 409