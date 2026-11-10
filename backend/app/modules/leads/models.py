from ...extensions import db
from ...shared.models import TimestampMixin

LEAD_STATUSES = ('new', 'contacted', 'qualified', 'converted', 'lost')
LEAD_SOURCES = ('web', 'facebook', 'instagram', 'whatsapp', 'linkedin', 'manual', 'other')
LEAD_ACTIVITY_TYPES = ('call', 'email', 'meeting', 'note')


class Lead(db.Model, TimestampMixin):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(50), nullable=False, default='manual')
    status = db.Column(db.String(30), nullable=False, default='new')
    notes = db.Column(db.Text, nullable=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customers.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    activities = db.relationship(
        'LeadActivity',
        back_populates='lead',
        cascade='all, delete-orphan',
        order_by='LeadActivity.id.asc()',
    )
    customer = db.relationship('Customer', foreign_keys=[customer_id])

    def to_dict(self, include_activities=False):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'source': self.source,
            'status': self.status,
            'notes': self.notes,
            'customer_id': self.customer_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_activities:
            data['activities'] = [a.to_dict() for a in self.activities]
        return data


class LeadActivity(db.Model, TimestampMixin):
    __tablename__ = 'lead_activities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lead_id = db.Column(
        db.Integer,
        db.ForeignKey('leads.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    activity_type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(150), nullable=True)

    lead = db.relationship('Lead', back_populates='activities')

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'activity_type': self.activity_type,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }