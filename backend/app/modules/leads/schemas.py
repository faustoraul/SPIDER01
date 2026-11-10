from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError
from .models import LEAD_STATUSES, LEAD_SOURCES, LEAD_ACTIVITY_TYPES


def _validate_choice(value, choices, field, default=None):
    if value is None:
        return default
    if not isinstance(value, str) or value not in choices:
        raise ValidationError(
            f"{field} debe ser uno de: {', '.join(choices)}."
        )
    return value


def _validate_notes(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError("El campo 'notes' debe ser texto.")
    return value.strip() or None


def validate_create_lead(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'source': _validate_choice(payload.get('source'), LEAD_SOURCES, 'source', default='manual'),
        'status': _validate_choice(payload.get('status'), LEAD_STATUSES, 'status', default='new'),
        'notes': _validate_notes(payload.get('notes')),
    }


def validate_update_lead(payload):
    """PUT: reemplazo completo de campos editables."""
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'source': _validate_choice(payload.get('source'), LEAD_SOURCES, 'source', default='manual'),
        'status': _validate_choice(payload.get('status'), LEAD_STATUSES, 'status', default='new'),
        'notes': _validate_notes(payload.get('notes')),
    }


def validate_patch_lead(payload):
    """PATCH: solo valida los campos presentes."""
    ensure_dict(payload)
    cleaned = {}
    if 'name' in payload:
        cleaned['name'] = require_string(payload, 'name', max_len=200)
    if 'email' in payload:
        cleaned['email'] = optional_string(payload, 'email', max_len=150)
    if 'phone' in payload:
        cleaned['phone'] = optional_string(payload, 'phone', max_len=50)
    if 'source' in payload:
        cleaned['source'] = _validate_choice(payload['source'], LEAD_SOURCES, 'source')
    if 'status' in payload:
        cleaned['status'] = _validate_choice(payload['status'], LEAD_STATUSES, 'status')
    if 'notes' in payload:
        cleaned['notes'] = _validate_notes(payload['notes'])
    return cleaned


def validate_create_activity(payload):
    ensure_dict(payload)
    return {
        'activity_type': _validate_choice(
            payload.get('activity_type'), LEAD_ACTIVITY_TYPES, 'activity_type'
        ),
        'notes': _validate_notes(payload.get('notes')),
        'created_by': optional_string(payload, 'created_by', max_len=150),
    }


def validate_public_lead(payload):
    """Valida el payload mínimo para captación pública."""
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'notes': _validate_notes(payload.get('notes')),
    }