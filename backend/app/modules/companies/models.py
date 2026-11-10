from ...extensions import db
from ...shared.models import TimestampMixin


class Company(db.Model, TimestampMixin):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    tax_id = db.Column(db.String(50), nullable=True, unique=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    branches = db.relationship(
        'Branch',
        back_populates='company',
        cascade='all, delete-orphan',
        lazy='select',
    )

    def to_dict(self, include_branches=False):
        data = {
            'id': self.id,
            'name': self.name,
            'tax_id': self.tax_id,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_branches:
            data['branches'] = [b.to_dict() for b in self.branches]
        return data