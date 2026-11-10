from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from .models import Category, Brand, Product, Inventory, InventoryMovement
from ..branches.models import Branch


# ---------- Categorías ----------

def list_categories(company_id):
    return Category.query.filter_by(company_id=company_id, is_active=True).all()

def create_category(company_id, data):
    if Category.query.filter_by(company_id=company_id, name=data['name']).first():
        raise ConflictError(f"Ya existe la categoría '{data['name']}'.")
    cat = Category(company_id=company_id, **data)
    db.session.add(cat)
    db.session.commit()
    return cat


# ---------- Marcas ----------

def list_brands(company_id):
    return Brand.query.filter_by(company_id=company_id, is_active=True).all()

def create_brand(company_id, data):
    if Brand.query.filter_by(company_id=company_id, name=data['name']).first():
        raise ConflictError(f"Ya existe la marca '{data['name']}'.")
    brand = Brand(company_id=company_id, **data)
    db.session.add(brand)
    db.session.commit()
    return brand


# ---------- Productos ----------

def list_products(company_id, search=None):
    query = Product.query.filter_by(company_id=company_id, is_active=True)
    if search:
        like = f'%{search}%'
        query = query.filter(db.or_(Product.name.ilike(like), Product.sku.ilike(like)))
    return query.order_by(Product.id.desc()).all()

def get_product(company_id, product_id):
    prod = Product.query.filter_by(id=product_id, company_id=company_id, is_active=True).first()
    if not prod:
        raise NotFoundError(f'Producto {product_id} no encontrado.')
    return prod

def create_product(company_id, data):
    if Product.query.filter_by(company_id=company_id, sku=data['sku']).first():
        raise ConflictError(f"Ya existe un producto con SKU '{data['sku']}'.")
    
    # Validar relaciones
    if data.get('category_id') and not Category.query.filter_by(id=data['category_id'], company_id=company_id).first():
        raise ValidationError("La categoría no existe o no pertenece a esta empresa.")
    if data.get('brand_id') and not Brand.query.filter_by(id=data['brand_id'], company_id=company_id).first():
        raise ValidationError("La marca no existe o no pertenece a esta empresa.")

    prod = Product(company_id=company_id, **data)
    db.session.add(prod)
    db.session.commit()
    return prod

def patch_product(company_id, product_id, data):
    prod = get_product(company_id, product_id)
    for key, value in data.items():
        setattr(prod, key, value)
    db.session.commit()
    return prod


# ---------- Inventario (Consultas) ----------

def get_branch_stock(company_id, branch_id):
    branch = Branch.query.filter_by(id=branch_id, company_id=company_id).first()
    if not branch:
        raise NotFoundError("Sucursal no encontrada en esta empresa.")
        
    inventories = Inventory.query.filter_by(branch_id=branch_id, company_id=company_id).all()
    result = []
    for inv in inventories:
        prod = db.session.get(Product, inv.product_id)
        if prod:
            result.append({
                'product_id': prod.id,
                'product_name': prod.name,
                'sku': prod.sku,
                'quantity': float(inv.quantity),
                'min_stock_alert': prod.min_stock_alert,
                'is_low_stock': float(inv.quantity) <= prod.min_stock_alert
            })
    return result


# ---------- Movimientos (Lógica Transaccional) ----------

def register_movement(company_id, data):
    # 1. Verificar sucursal y producto
    branch = Branch.query.filter_by(id=data['branch_id'], company_id=company_id).first()
    if not branch:
        raise ValidationError("La sucursal no existe o no pertenece a esta empresa.")
    
    product = Product.query.filter_by(id=data['product_id'], company_id=company_id, is_active=True).first()
    if not product:
        raise ValidationError("El producto no existe o no pertenece a esta empresa.")

    # 2. Obtener o crear el registro de inventario para esta sucursal/producto
    inv = Inventory.query.filter_by(
        company_id=company_id, branch_id=branch.id, product_id=product.id
    ).with_for_update().first()  # Bloqueo pesimista para evitar race conditions

    if not inv:
        inv = Inventory(company_id=company_id, branch_id=branch.id, product_id=product.id, quantity=0)
        db.session.add(inv)
        db.session.flush()

    current_qty = float(inv.quantity)
    move_qty = float(data['quantity'])
    m_type = data['movement_type']

    # 3. Calcular nueva cantidad según el tipo
    if m_type == 'in':
        new_qty = current_qty + move_qty
    elif m_type == 'out':
        if current_qty < move_qty:
            raise ValidationError(f"Stock insuficiente. Disponible: {current_qty}, Solicitado: {move_qty}.")
        new_qty = current_qty - move_qty
    elif m_type == 'adjustment':
        new_qty = move_qty  # Ajuste absoluto (conteo físico)
    else:
        raise ValidationError("Tipo de movimiento inválido.")

    if new_qty < 0:
        raise ValidationError("El movimiento resultaría en stock negativo. Operación cancelada.")

    # 4. Aplicar cambios y registrar el historial
    inv.quantity = new_qty
    movement = InventoryMovement(
        company_id=company_id,
        branch_id=branch.id,
        product_id=product.id,
        movement_type=m_type,
        quantity=move_qty,
        reference=data.get('reference'),
        notes=data.get('notes'),
        created_by=data.get('created_by')
    )
    
    db.session.add(movement)
    db.session.commit()  # Transacción atómica: si algo falla, no se guarda nada
    return movement