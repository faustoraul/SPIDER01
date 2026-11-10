from ...extensions import db
from ...shared.models import TimestampMixin


class Branch(db.Model, TimestampMixin):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    company = db.relationship('Company', back_populates='branches')

    __table_args__ = (
        db.UniqueConstraint('company_id', 'code', name='uq_branch_company_code'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }