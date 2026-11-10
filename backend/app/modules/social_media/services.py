import json

from ...extensions import db
from ...core.exceptions import NotFoundError, ValidationError, ConflictError
from .models import SocialAccount, WebhookEvent, PROVIDERS
from .adapters import get_adapter
from ..leads.models import Lead


# ---------- Cuentas Sociales ----------

def list_accounts(company_id):
    return SocialAccount.query.filter_by(company_id=company_id) \
        .order_by(SocialAccount.id.asc()).all()


def create_account(company_id, data):
    provider = data.get('provider')
    if provider not in PROVIDERS:
        raise ValidationError(
            f"provider debe ser uno de: {', '.join(PROVIDERS)}."
        )
    if not data.get('external_account_id'):
        raise ValidationError("external_account_id es obligatorio.")

    existing = SocialAccount.query.filter_by(
        company_id=company_id,
        provider=provider,
        external_account_id=data['external_account_id'],
    ).first()
    if existing:
        raise ConflictError(
            f"Ya existe una cuenta '{provider}' con ese external_account_id en esta empresa."
        )

    account = SocialAccount(
        company_id=company_id,
        provider=provider,
        external_account_id=data['external_account_id'],
        access_token=data.get('access_token'),
    )
    db.session.add(account)
    db.session.commit()
    return account


def delete_account(company_id, account_id):
    account = SocialAccount.query.filter_by(
        id=account_id, company_id=company_id
    ).first()
    if not account:
        raise NotFoundError(f'Cuenta social {account_id} no encontrada.')
    db.session.delete(account)
    db.session.commit()


# ---------- Webhooks ----------

def list_events(company_id, status=None, provider=None):
    query = WebhookEvent.query.filter_by(company_id=company_id)
    if status:
        query = query.filter_by(status=status)
    if provider:
        query = query.filter_by(provider=provider)
    return query.order_by(WebhookEvent.id.desc()).all()


def _process_event(event):
    """
    Procesa el payload de un WebhookEvent, usando el adaptador correspondiente.
    Crea un Lead si el payload es válido.
    """
    adapter = get_adapter(event.provider)
    try:
        payload = json.loads(event.payload)
    except (ValueError, TypeError) as e:
        raise ValidationError(f'Payload no es JSON válido: {e}')

    cleaned = adapter.parse_webhook(payload)

    lead = Lead(
        company_id=event.company_id,
        name=cleaned['name'],
        email=cleaned['email'],
        phone=cleaned['phone'],
        source=event.provider,
        status='new',
        notes=cleaned.get('message'),
    )
    db.session.add(lead)
    event.status = 'processed'
    event.error_message = None
    db.session.commit()
    return lead


def handle_webhook(company_id, provider, payload):
    """
    Punto de entrada de un webhook.
    1. Crea el evento con status='pending'.
    2. Intenta procesarlo inmediatamente.
    3. Si falla, lo deja con status='failed' y guarda el error.
    """
    if provider not in PROVIDERS:
        raise ValidationError(f"Proveedor '{provider}' no soportado.")

    if not isinstance(payload, dict):
        raise ValidationError('El payload del webhook debe ser un objeto JSON.')

    event = WebhookEvent(
        company_id=company_id,
        provider=provider,
        payload=json.dumps(payload),
        status='pending',
    )
    db.session.add(event)
    db.session.commit()

    try:
        lead = _process_event(event)
        return event, lead
    except ValidationError as e:
        event.status = 'failed'
        event.error_message = str(e)
        db.session.commit()
        raise


def retry_event(company_id, event_id):
    """Reintenta procesar un evento fallido."""
    event = WebhookEvent.query.filter_by(
        id=event_id, company_id=company_id
    ).first()
    if not event:
        raise NotFoundError(f'Evento {event_id} no encontrado.')
    if event.status == 'processed':
        raise ConflictError('Este evento ya fue procesado.')

    event.status = 'pending'
    event.error_message = None
    db.session.commit()

    try:
        lead = _process_event(event)
        return event, lead
    except ValidationError as e:
        event.status = 'failed'
        event.error_message = str(e)
        db.session.commit()
        raise