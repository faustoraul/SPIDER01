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


def _create_category(client, cid, name='Electrónica'):
    r = client.post(f'/api/companies/{cid}/categories', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_brand(client, cid, name='Sony'):
    r = client.post(f'/api/companies/{cid}/brands', json={'name': name})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _create_product(client, cid, sku='SKU-001', name='Producto X', **overrides):
    payload = {'sku': sku, 'name': name, 'cost_price': 100, 'sale_price': 150}
    payload.update(overrides)
    r = client.post(f'/api/companies/{cid}/products', json=payload)
    assert r.status_code == 201, r.get_json()
    return r.get_json()['id']


def _register_movement(client, cid, branch_id, product_id, m_type, qty):
    r = client.post(f'/api/companies/{cid}/inventory/movements', json={
        'branch_id': branch_id, 'product_id': product_id,
        'movement_type': m_type, 'quantity': qty,
    })
    return r


# ---------- Categorías y Marcas ----------

def test_create_category(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/categories', json={'name': 'Ropa'})
    assert r.status_code == 201
    assert r.get_json()['name'] == 'Ropa'


def test_duplicate_category_conflict(client):
    cid = _create_company(client)
    _create_category(client, cid, 'Electrónica')
    r = client.post(f'/api/companies/{cid}/categories', json={'name': 'Electrónica'})
    assert r.status_code == 409


def test_create_brand(client):
    cid = _create_company(client)
    r = client.post(f'/api/companies/{cid}/brands', json={'name': 'Nike'})
    assert r.status_code == 201
    assert r.get_json()['name'] == 'Nike'


# ---------- Productos ----------

def test_create_product_with_relations(client):
    cid = _create_company(client)
    cat_id = _create_category(client, cid)
    brand_id = _create_brand(client, cid)
    r = client.post(f'/api/companies/{cid}/products', json={
        'sku': 'ELEC-001', 'name': 'Laptop', 'category_id': cat_id,
        'brand_id': brand_id, 'cost_price': 800, 'sale_price': 1200, 'tax_rate': 18,
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body['category_name'] == 'Electrónica'
    assert body['brand_name'] == 'Sony'
    assert body['sale_price'] == 1200.0


def test_duplicate_sku_conflict(client):
    cid = _create_company(client)
    _create_product(client, cid, sku='DUP-001')
    r = client.post(f'/api/companies/{cid}/products', json={'sku': 'DUP-001', 'name': 'Otro'})
    assert r.status_code == 409


def test_products_isolation(client):
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    _create_product(client, c1, sku='C1-SKU')
    _create_product(client, c2, sku='C2-SKU')

    r = client.get(f'/api/companies/{c1}/products')
    items = r.get_json()['items']
    assert len(items) == 1
    assert items[0]['sku'] == 'C1-SKU'


def test_create_product_invalid_category_other_company(client):
    """No se puede asignar categoría de otra empresa."""
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    cat_c2 = _create_category(client, c2, 'CatC2')
    
    r = client.post(f'/api/companies/{c1}/products', json={
        'sku': 'X', 'name': 'X', 'category_id': cat_c2,
    })
    assert r.status_code == 422


# ---------- Movimientos de Inventario ----------

def test_movement_in_creates_stock(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    
    r = _register_movement(client, cid, bid, pid, 'in', 50)
    assert r.status_code == 201
    assert r.get_json()['movement_type'] == 'in'
    
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    stock = r.get_json()
    assert len(stock) == 1
    assert stock[0]['quantity'] == 50.0


def test_movement_out_decreases_stock(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    
    _register_movement(client, cid, bid, pid, 'in', 20)
    r = _register_movement(client, cid, bid, pid, 'out', 5)
    assert r.status_code == 201
    
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    assert r.get_json()[0]['quantity'] == 15.0


def test_movement_out_insufficient_stock_422(client):
    """Regla #8: no se permiten existencias negativas."""
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    
    _register_movement(client, cid, bid, pid, 'in', 5)
    r = _register_movement(client, cid, bid, pid, 'out', 10)
    assert r.status_code == 422
    assert 'Stock insuficiente' in r.get_json()['message']
    
    # Verificar que el stock NO cambió (rollback)
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    assert r.get_json()[0]['quantity'] == 5.0


def test_movement_adjustment_sets_absolute(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    pid = _create_product(client, cid)
    
    _register_movement(client, cid, bid, pid, 'in', 100)
    # Ajuste por conteo físico: hay 97 en realidad
    _register_movement(client, cid, bid, pid, 'adjustment', 97)
    
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    assert r.get_json()[0]['quantity'] == 97.0


def test_movement_cross_tenant_branch_rejected(client):
    """No se puede usar una sucursal de otra empresa."""
    c1 = _create_company(client, name='C1')
    c2 = _create_company(client, name='C2')
    pid_c1 = _create_product(client, c1)
    bid_c2 = _create_branch(client, c2)
    
    r = _register_movement(client, c1, bid_c2, pid_c1, 'in', 10)
    assert r.status_code == 422


def test_low_stock_flag(client):
    cid = _create_company(client)
    bid = _create_branch(client, cid)
    
    # Producto con min_stock_alert=10
    pid = _create_product(client, cid, min_stock_alert=10)
    _register_movement(client, cid, bid, pid, 'in', 5)  # Por debajo del mínimo
    
    r = client.get(f'/api/companies/{cid}/branches/{bid}/inventory')
    assert r.get_json()[0]['is_low_stock'] is True