from ...extensions import db
from ...shared.models import TimestampMixin

MOVEMENT_TYPES = ('in', 'out', 'adjustment')


class Category(db.Model, TimestampMixin):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uq_category_company_name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
        }


class Brand(db.Model, TimestampMixin):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uq_brand_company_name'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'is_active': self.is_active,
        }


class Product(db.Model, TimestampMixin):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    brand_id = db.Column(
        db.Integer,
        db.ForeignKey('brands.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    sku = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    unit_measure = db.Column(db.String(50), nullable=False, default='unit')
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    min_stock_alert = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    category = db.relationship('Category')
    brand = db.relationship('Brand')

    __table_args__ = (
        db.UniqueConstraint('company_id', 'sku', name='uq_product_company_sku'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'sku': self.sku,
            'barcode': self.barcode,
            'name': self.name,
            'description': self.description,
            'unit_measure': self.unit_measure,
            'cost_price': float(self.cost_price) if self.cost_price else 0.0,
            'sale_price': float(self.sale_price) if self.sale_price else 0.0,
            'tax_rate': float(self.tax_rate) if self.tax_rate else 0.0,
            'min_stock_alert': self.min_stock_alert,
            'is_active': self.is_active,
        }


class Inventory(db.Model, TimestampMixin):
    __tablename__ = 'inventories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    branch_id = db.Column(
        db.Integer,
        db.ForeignKey('branches.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('branch_id', 'product_id', name='uq_inventory_branch_product'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'product_id': self.product_id,
            'quantity': float(self.quantity),
        }


class InventoryMovement(db.Model, TimestampMixin):
    __tablename__ = 'inventory_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    branch_id = db.Column(
        db.Integer,
        db.ForeignKey('branches.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'branch_id': self.branch_id,
            'product_id': self.product_id,
            'movement_type': self.movement_type,
            'quantity': float(self.quantity),
            'reference': self.reference,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }