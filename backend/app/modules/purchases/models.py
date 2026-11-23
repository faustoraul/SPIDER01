from ...extensions import db
from ...shared.models import TimestampMixin

PURCHASE_STATUSES = ('draft', 'ordered', 'received', 'cancelled')


class Supplier(db.Model, TimestampMixin):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    tax_id = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uq_supplier_company_name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'tax_id': self.tax_id,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PurchaseOrder(db.Model, TimestampMixin):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('suppliers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    branch_id = db.Column(
        db.Integer,
        db.ForeignKey('branches.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    order_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    order_date = db.Column(db.Date, nullable=False)
    expected_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    supplier = db.relationship('Supplier')
    branch = db.relationship('Branch')
    items = db.relationship(
        'PurchaseOrderItem',
        back_populates='order',
        cascade='all, delete-orphan',
        order_by='PurchaseOrderItem.id.asc()',
    )

    __table_args__ = (
        db.UniqueConstraint('company_id', 'order_number', name='uq_purchase_order_number'),
    )

    def to_dict(self, include_items=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'branch_id': self.branch_id,
            'order_number': self.order_number,
            'status': self.status,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'notes': self.notes,
            'total': float(self.total),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            data['items'] = [i.to_dict() for i in self.items]
        return data


class PurchaseOrderItem(db.Model, TimestampMixin):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('purchase_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False)

    order = db.relationship('PurchaseOrder', back_populates='items')
    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sku': self.product.sku if self.product else None,
            'quantity': float(self.quantity),
            'unit_cost': float(self.unit_cost),
            'subtotal': float(self.quantity * self.unit_cost),
        }