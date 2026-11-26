from ...extensions import db
from ...shared.models import TimestampMixin

SALE_STATUSES = ('quote', 'order', 'invoiced', 'paid', 'cancelled')


class Sale(db.Model, TimestampMixin):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='RESTRICT'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=True, index=True)
    
    sale_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='invoiced')
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    notes = db.Column(db.Text, nullable=True)

    customer = db.relationship('Customer')
    branch = db.relationship('Branch')
    items = db.relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan', order_by='SaleItem.id.asc()')

    __table_args__ = (db.UniqueConstraint('company_id', 'sale_number', name='uq_sale_number'),)

    def to_dict(self, include_items=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Consumidor Final',
            'sale_number': self.sale_number,
            'status': self.status,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'total': float(self.total),
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            data['items'] = [i.to_dict() for i in self.items]
        return data


class SaleItem(db.Model, TimestampMixin):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    discount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sku': self.product.sku if self.product else None,
            'quantity': float(self.quantity),
            'unit_price': float(self.unit_price),
            'tax_rate': float(self.tax_rate),
            'discount': float(self.discount),
            'subtotal': float((self.quantity * self.unit_price) - self.discount),
        }

        

# =====================================================================
# MODELOS DE PUNTO DE VENTA (POS)
# =====================================================================

PAYMENT_METHODS = ('cash', 'card', 'transfer', 'credit', 'mixed')
CASH_SESSION_STATUSES = ('open', 'closed')


class CashRegister(db.Model, TimestampMixin):
    """Caja registradora física. Cada sucursal puede tener varias."""
    __tablename__ = 'cash_registers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('branch_id', 'name', name='uq_cash_register_branch_name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'name': self.name,
            'is_active': self.is_active,
        }


class CashSession(db.Model, TimestampMixin):
    """Turno de caja: desde apertura hasta cierre."""
    __tablename__ = 'cash_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    cash_register_id = db.Column(db.Integer, db.ForeignKey('cash_registers.id', ondelete='RESTRICT'), nullable=False, index=True)
    user_name = db.Column(db.String(150), nullable=False)  # En FASE 16 será user_id (FK)
    status = db.Column(db.String(20), nullable=False, default='open')
    opening_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    closing_amount = db.Column(db.Numeric(12, 2), nullable=True)
    expected_amount = db.Column(db.Numeric(12, 2), nullable=True)  # Calculado al cerrar
    difference = db.Column(db.Numeric(12, 2), nullable=True)  # Sobrante/Faltante
    opened_at = db.Column(db.DateTime, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    register = db.relationship('CashRegister')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'cash_register_id': self.cash_register_id,
            'register_name': self.register.name if self.register else None,
            'user_name': self.user_name,
            'status': self.status,
            'opening_amount': float(self.opening_amount),
            'closing_amount': float(self.closing_amount) if self.closing_amount is not None else None,
            'expected_amount': float(self.expected_amount) if self.expected_amount is not None else None,
            'difference': float(self.difference) if self.difference is not None else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'notes': self.notes,
        }


class Payment(db.Model, TimestampMixin):
    """Pago asociado a una venta. Una venta puede tener varios pagos (pago mixto)."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False, index=True)
    cash_session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id', ondelete='RESTRICT'), nullable=True, index=True)
    method = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reference = db.Column(db.String(100), nullable=True)  # Para transferencias / tarjetas
    notes = db.Column(db.Text, nullable=True)

    sale = db.relationship('Sale', backref='payments')
    cash_session = db.relationship('CashSession')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'sale_id': self.sale_id,
            'cash_session_id': self.cash_session_id,
            'method': self.method,
            'amount': float(self.amount),
            'reference': self.reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }