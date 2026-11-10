from ...extensions import db
from ...shared.models import TimestampMixin

PROVIDERS = ('facebook', 'instagram', 'whatsapp', 'messenger', 'tiktok', 'youtube', 'linkedin')

class SocialAccount(db.Model, TimestampMixin):
    __tablename__ = 'social_accounts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    provider = db.Column(db.String(50), nullable=False)
    external_account_id = db.Column(db.String(150), nullable=False)
    access_token = db.Column(db.Text, nullable=True) # En producción debe ir encriptado
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'provider', 'external_account_id', name='uq_social_account'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'provider': self.provider,
            'external_account_id': self.external_account_id,
            # Omitimos el access_token por seguridad
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WebhookEvent(db.Model, TimestampMixin):
    __tablename__ = 'webhook_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    provider = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending') # pending, processed, failed
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'provider': self.provider,
            'status': self.status,
            'payload': self.payload,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }