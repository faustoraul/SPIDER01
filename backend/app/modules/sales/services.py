from datetime import datetime
from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from .models import Sale, SaleItem, Payment, CashRegister, CashSession
from ..inventory.models import Product, Inventory, InventoryMovement
from ..branches.models import Branch
from ..crm.models import Customer

# ---------- Cajas Registradoras ----------

def list_cash_registers(company_id):
    return CashRegister.query.filter_by(company_id=company_id, is_active=True).all()

def create_cash_register(company_id, data):
    if not Branch.query.filter_by(id=data['branch_id'], company_id=company_id).first():
        raise ValidationError("La sucursal no pertenece a esta empresa.")
    if CashRegister.query.filter_by(company_id=company_id, branch_id=data['branch_id'], name=data['name']).first():
        raise ConflictError(f"Ya existe una caja '{data['name']}' en esta sucursal.")
    
    reg = CashRegister(company_id=company_id, branch_id=data['branch_id'], name=data['name'])
    db.session.add(reg)
    db.session.commit()
    return reg

# ---------- Turnos de Caja ----------

def open_session(company_id, data):
    reg = CashRegister.query.filter_by(id=data['cash_register_id'], company_id=company_id).first()
    if not reg:
        raise ValidationError("La caja no pertenece a esta empresa.")
    
    # Verificar que no haya un turno abierto
    existing = CashSession.query.filter_by(company_id=company_id, cash_register_id=reg.id, status='open').first()
    if existing:
        raise ConflictError("Esta caja ya tiene un turno abierto. Debes cerrarlo primero.")

    session = CashSession(
        company_id=company_id,
        cash_register_id=reg.id,
        user_name=data['user_name'],
        opening_amount=data['opening_amount'],
        opened_at=datetime.utcnow(),
        status='open'
    )
    db.session.add(session)
    db.session.commit()
    return session

def close_session(company_id, session_id, data):
    session = CashSession.query.filter_by(id=session_id, company_id=company_id).first()
    if not session:
        raise NotFoundError("Turno no encontrado.")
    if session.status == 'closed':
        raise ConflictError("Este turno ya fue cerrado.")

    # Calcular el efectivo esperado: Apertura + Pagos en efectivo
    cash_payments = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.cash_session_id == session.id,
        Payment.method == 'cash'
    ).scalar() or 0.0

    expected = float(session.opening_amount) + float(cash_payments)
    closing = data['closing_amount']
    difference = closing - expected

    session.closing_amount = closing
    session.expected_amount = expected
    session.difference = difference
    session.closed_at = datetime.utcnow()
    session.status = 'closed'
    session.notes = data.get('notes')
    db.session.commit()
    return session

def list_sessions(company_id, status=None):
    query = CashSession.query.filter_by(company_id=company_id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(CashSession.id.desc()).all()

# ---------- Ventas (Lógica Transaccional) ----------

def list_sales(company_id, status=None):
    query = Sale.query.filter_by(company_id=company_id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Sale.id.desc()).all()

def get_sale(company_id, sale_id):
    sale = Sale.query.filter_by(id=sale_id, company_id=company_id).first()
    if not sale:
        raise NotFoundError("Venta no encontrada.")
    return sale

def create_sale(company_id, data):
    """
    El núcleo del sistema. Registra la venta, descuenta inventario, procesa pagos y actualiza caja.
    Todo es atómico (un solo commit al final).
    """
    # 1. Validar sucursal y cliente
    if not Branch.query.filter_by(id=data['branch_id'], company_id=company_id).first():
        raise ValidationError("La sucursal no pertenece a esta empresa.")
    
    if data['customer_id']:
        if not Customer.query.filter_by(id=data['customer_id'], company_id=company_id).first():
            raise ValidationError("El cliente no pertenece a esta empresa.")

    if Sale.query.filter_by(company_id=company_id, sale_number=data['sale_number']).first():
        raise ConflictError(f"Ya existe una venta con el número '{data['sale_number']}'.")

    # 2. Procesar Ítems, validar stock y calcular totales
    sale_items = []
    subtotal = 0.0
    tax_amount = 0.0
    discount_amount = 0.0

    for item_data in data['items']:
        product = Product.query.filter_by(id=item_data['product_id'], company_id=company_id, is_active=True).first()
        if not product:
            raise ValidationError(f"El producto {item_data['product_id']} no existe o está inactivo.")

        # Verificar Stock (Usamos bloqueo pesimista)
        inv = Inventory.query.filter_by(
            company_id=company_id, branch_id=data['branch_id'], product_id=product.id
        ).with_for_update().first()

        if not inv or inv.quantity < item_data['quantity']:
            available = inv.quantity if inv else 0
            raise ValidationError(f"Stock insuficiente para '{product.name}'. Disponible: {available}, Solicitado: {item_data['quantity']}.")

        # Calcular línea
        line_base = (item_data['quantity'] * item_data['unit_price']) - item_data['discount']
        line_tax = line_base * (item_data['tax_rate'] / 100)
        
        subtotal += line_base
        tax_amount += line_tax
        discount_amount += item_data['discount']

        sale_items.append({
            'product_id': product.id,
            'quantity': item_data['quantity'],
            'unit_price': item_data['unit_price'],
            'tax_rate': item_data['tax_rate'],
            'discount': item_data['discount'],
        })

    total = subtotal + tax_amount

    # 3. Crear Cabecera de Venta
    sale = Sale(
        company_id=company_id,
        branch_id=data['branch_id'],
        customer_id=data['customer_id'],
        sale_number=data['sale_number'],
        issue_date=data['issue_date'],
        due_date=data.get('due_date'),
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total=total,
        notes=data.get('notes'),
        status='invoiced'
    )
    db.session.add(sale)
    db.session.flush() # Para obtener el ID

    # 4. Guardar Ítems y Descontar Stock
    for item in sale_items:
        # Guardar ítem
        db.session.add(SaleItem(sale_id=sale.id, **item))

        # Descontar Stock
        inv = Inventory.query.filter_by(
            company_id=company_id, branch_id=data['branch_id'], product_id=item['product_id']
        ).first()
        from decimal import Decimal
        inv.quantity = inv.quantity - Decimal(str(item['quantity']))

        # Registrar Movimiento
        db.session.add(InventoryMovement(
            company_id=company_id,
            branch_id=data['branch_id'],
            product_id=item['product_id'],
            movement_type='out',
            quantity=item['quantity'],
            reference=f"Venta #{sale.sale_number}",
            notes="Salida por POS"
        ))

    # 5. Procesar Pagos
    total_paid = 0.0
    for p_data in data.get('payments', []):
        payment = Payment(
            company_id=company_id,
            sale_id=sale.id,
            method=p_data['method'],
            amount=p_data['amount'],
            reference=p_data.get('reference'),
            notes=p_data.get('notes')
        )

        # Si es efectivo, asociar al turno de caja abierto
        if p_data['method'] == 'cash':
            open_session = CashSession.query.filter_by(
                company_id=company_id, status='open'
            ).first()
            if not open_session:
                raise ValidationError("No se puede cobrar en efectivo sin un turno de caja abierto.")
            payment.cash_session_id = open_session.id

        db.session.add(payment)
        total_paid += p_data['amount']

    # 6. Actualizar estado de la venta
    if total_paid >= total:
        sale.status = 'paid'
    
    db.session.commit()
    return sale