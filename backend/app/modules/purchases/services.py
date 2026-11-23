from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from ..inventory.models import Product, Inventory, InventoryMovement
from ..branches.models import Branch


# ---------- Proveedores ----------

def list_suppliers(company_id):
    return Supplier.query.filter_by(company_id=company_id, is_active=True).order_by(Supplier.id.asc()).all()


def create_supplier(company_id, data):
    if Supplier.query.filter_by(company_id=company_id, name=data['name']).first():
        raise ConflictError(f"Ya existe un proveedor con el nombre '{data['name']}'.")
    supplier = Supplier(company_id=company_id, **data)
    db.session.add(supplier)
    db.session.commit()
    return supplier


# ---------- Órdenes de Compra ----------

def list_orders(company_id, status=None):
    query = PurchaseOrder.query.filter_by(company_id=company_id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(PurchaseOrder.id.desc()).all()


def get_order(company_id, order_id):
    order = PurchaseOrder.query.filter_by(id=order_id, company_id=company_id).first()
    if not order:
        raise NotFoundError(f'Orden de compra {order_id} no encontrada.')
    return order


def create_order(company_id, data):
    # 1. Validar relaciones
    if not Supplier.query.filter_by(id=data['supplier_id'], company_id=company_id).first():
        raise ValidationError("El proveedor no existe o no pertenece a esta empresa.")
    
    if not Branch.query.filter_by(id=data['branch_id'], company_id=company_id).first():
        raise ValidationError("La sucursal no existe o no pertenece a esta empresa.")

    if PurchaseOrder.query.filter_by(company_id=company_id, order_number=data['order_number']).first():
        raise ConflictError(f"Ya existe una orden con el número '{data['order_number']}'.")

    # 2. Validar productos y calcular total
    total = 0
    for item_data in data['items']:
        product = Product.query.filter_by(id=item_data['product_id'], company_id=company_id).first()
        if not product:
            raise ValidationError(f"El producto {item_data['product_id']} no existe o no pertenece a esta empresa.")
        total += item_data['quantity'] * item_data['unit_cost']

    # 3. Crear cabecera
    order = PurchaseOrder(
        company_id=company_id,
        supplier_id=data['supplier_id'],
        branch_id=data['branch_id'],
        order_number=data['order_number'],
        order_date=data['order_date'],
        expected_date=data.get('expected_date'),
        notes=data.get('notes'),
        total=total,
        status='draft'
    )
    db.session.add(order)
    db.session.flush()  # Para obtener el order.id

    # 4. Crear ítems
    for item_data in data['items']:
        item = PurchaseOrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_cost=item_data['unit_cost']
        )
        db.session.add(item)

    db.session.commit()
    return order


def patch_order(company_id, order_id, data):
    order = get_order(company_id, order_id)
    for key, value in data.items():
        setattr(order, key, value)
    db.session.commit()
    return order


def receive_order(company_id, order_id):
    """
    Lógica transaccional: recibe la mercancía y actualiza el inventario de la FASE 8.
    """
    order = get_order(company_id, order_id)

    if order.status == 'received':
        raise ConflictError('Esta orden ya fue recibida anteriormente.')
    if order.status == 'cancelled':
        raise ConflictError('No se puede recibir una orden cancelada.')

    for item in order.items:
        # Buscar registro de inventario con bloqueo (evita condiciones de carrera)
        inv = Inventory.query.filter_by(
            company_id=company_id, branch_id=order.branch_id, product_id=item.product_id
        ).with_for_update().first()

        if not inv:
            inv = Inventory(company_id=company_id, branch_id=order.branch_id, product_id=item.product_id, quantity=0)
            db.session.add(inv)

        # Sumar al stock
        inv.quantity += item.quantity

        # Registrar el movimiento de entrada
        movement = InventoryMovement(
            company_id=company_id,
            branch_id=order.branch_id,
            product_id=item.product_id,
            movement_type='in',
            quantity=item.quantity,
            reference=f"Compra #{order.order_number}",
            notes=f"Recepción de orden {order.order_number}"
        )
        db.session.add(movement)

    order.status = 'received'
    db.session.commit()  # Todo se guarda o falla en bloque
    return order