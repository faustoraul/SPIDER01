from ...extensions import db
from ...shared.models import TimestampMixin

STAGES = [
    ('prospecting', 'Prospección', 1),
    ('qualification', 'Calificación', 2),
    ('proposal', 'Propuesta', 3),
    ('negotiation', 'Negociación', 4),
    ('closed_won', 'Cerrada Ganada', 5),
    ('closed_lost', 'Cerrada Perdida', 6),
]


class PipelineStage(db.Model, TimestampMixin):
    __tablename__ = 'pipeline_stages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'code', name='uq_stage_company_code'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'code': self.code,
            'order_index': self.order_index,
            'is_active': self.is_active,
        }


class Opportunity(db.Model, TimestampMixin):
    __tablename__ = 'opportunities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customers.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    stage_id = db.Column(
        db.Integer,
        db.ForeignKey('pipeline_stages.id'),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    expected_close_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    customer = db.relationship('Customer', backref='opportunities')
    stage = db.relationship('PipelineStage')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'stage_id': self.stage_id,
            'stage_name': self.stage.name if self.stage else None,
            'stage_code': self.stage.code if self.stage else None,
            'name': self.name,
            'amount': float(self.amount) if self.amount is not None else 0.0,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }