from ...extensions import db
from ...shared.models import TimestampMixin

CUSTOMER_TYPES = ('individual', 'company')


class Customer(db.Model, TimestampMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    customer_type = db.Column(db.String(20), nullable=False, default='individual')
    identification = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    contacts = db.relationship(
        'Contact',
        back_populates='customer',
        cascade='all, delete-orphan',
        order_by='Contact.id.asc()',
        lazy='select',
    )

    __table_args__ = (
        db.UniqueConstraint('company_id', 'identification', name='uq_customer_company_identification'),
        db.UniqueConstraint('company_id', 'email', name='uq_customer_company_email'),
    )

    def to_dict(self, include_contacts=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'customer_type': self.customer_type,
            'identification': self.identification,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_contacts:
            data['contacts'] = [c.to_dict() for c in self.contacts]
        return data


class Contact(db.Model, TimestampMixin):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customers.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)

    customer = db.relationship('Customer', back_populates='contacts')

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'position': self.position,
            'email': self.email,
            'phone': self.phone,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }