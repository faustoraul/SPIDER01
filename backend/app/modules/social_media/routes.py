from flask import Blueprint, jsonify, request

from . import services
from .models import PROVIDERS
from ..companies import services as company_services

social_bp = Blueprint(
    'social_media',
    __name__,
    url_prefix='/api/companies/<int:company_id>/social',
)


# ---------- Cuentas Sociales ----------

@social_bp.route('/accounts', methods=['GET'])
def list_accounts(company_id):
    company_services.get_company(company_id)
    accounts = services.list_accounts(company_id)
    return jsonify([a.to_dict() for a in accounts]), 200


@social_bp.route('/accounts', methods=['POST'])
def create_account(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({
            'error': 'validation_error',
            'message': 'Se requiere un JSON en el cuerpo.',
        }), 422
    account = services.create_account(company_id, payload)
    return jsonify(account.to_dict()), 201


@social_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(company_id, account_id):
    services.delete_account(company_id, account_id)
    return '', 204


# ---------- Webhooks ----------

@social_bp.route('/webhooks', methods=['GET'])
def list_events(company_id):
    company_services.get_company(company_id)
    status = request.args.get('status', type=str)
    provider = request.args.get('provider', type=str)
    events = services.list_events(company_id, status=status, provider=provider)
    return jsonify({
        'items': [e.to_dict() for e in events],
        'total': len(events),
    }), 200


@social_bp.route('/webhooks/<provider>', methods=['POST'])
def receive_webhook(company_id, provider):
    """
    Recibe webhooks de redes sociales.
    NOTA: en producción este endpoint irá fuera del prefijo /api/companies
    y usará verificación de firma del proveedor (FASE 21).
    En esta fase, `company_id` viene en la URL porque no hay verificación
    de firma todavía; se considera un endpoint de simulación/desarrollo.
    """
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    try:
        event, lead = services.handle_webhook(company_id, provider, payload)
        return jsonify({
            'event_id': event.id,
            'status': event.status,
            'lead_id': lead.id,
        }), 201
    except Exception:
        # El evento ya se guardó como 'failed' antes de lanzar.
        from .models import WebhookEvent
        from ...extensions import db
        failed = WebhookEvent.query.filter_by(
            company_id=company_id, provider=provider
        ).order_by(WebhookEvent.id.desc()).first()
        return jsonify({
            'event_id': failed.id if failed else None,
            'status': 'failed',
            'error': failed.error_message if failed else 'Error desconocido',
        }), 422


@social_bp.route('/webhooks/<int:event_id>/retry', methods=['POST'])
def retry_event(company_id, event_id):
    try:
        event, lead = services.retry_event(company_id, event_id)
        return jsonify({
            'event_id': event.id,
            'status': event.status,
            'lead_id': lead.id,
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'processing_error',
            'message': str(e),
        }), 422