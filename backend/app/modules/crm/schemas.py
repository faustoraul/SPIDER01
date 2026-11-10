from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError
from .models import CUSTOMER_TYPES


def _validate_customer_type(value):
    if value is None:
        return 'individual'
    if not isinstance(value, str) or value not in CUSTOMER_TYPES:
        raise ValidationError(
            f"customer_type debe ser uno de: {', '.join(CUSTOMER_TYPES)}."
        )
    return value


def _validate_notes(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError("El campo 'notes' debe ser texto.")
    return value.strip() or None


def validate_create_customer(payload):
    ensure_dict(payload)
    return {
        'customer_type': _validate_customer_type(payload.get('customer_type')),
        'identification': optional_string(payload, 'identification', max_len=50),
        'name': require_string(payload, 'name', max_len=200),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'address': optional_string(payload, 'address', max_len=500),
        'notes': _validate_notes(payload.get('notes')),
    }


def validate_update_customer(payload):
    """PUT: reemplazo completo."""
    ensure_dict(payload)
    return {
        'customer_type': _validate_customer_type(payload.get('customer_type')),
        'identification': optional_string(payload, 'identification', max_len=50),
        'name': require_string(payload, 'name', max_len=200),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'address': optional_string(payload, 'address', max_len=500),
        'notes': _validate_notes(payload.get('notes')),
    }


def validate_patch_customer(payload):
    """PATCH: solo valida los campos presentes."""
    ensure_dict(payload)
    cleaned = {}
    if 'customer_type' in payload:
        cleaned['customer_type'] = _validate_customer_type(payload['customer_type'])
    if 'identification' in payload:
        cleaned['identification'] = optional_string(payload, 'identification', max_len=50)
    if 'name' in payload:
        cleaned['name'] = require_string(payload, 'name', max_len=200)
    if 'email' in payload:
        cleaned['email'] = optional_string(payload, 'email', max_len=150)
    if 'phone' in payload:
        cleaned['phone'] = optional_string(payload, 'phone', max_len=50)
    if 'address' in payload:
        cleaned['address'] = optional_string(payload, 'address', max_len=500)
    if 'notes' in payload:
        cleaned['notes'] = _validate_notes(payload['notes'])
    return cleaned


def validate_create_contact(payload):
    ensure_dict(payload)
    return {
        'first_name': require_string(payload, 'first_name', max_len=100),
        'last_name': optional_string(payload, 'last_name', max_len=100),
        'position': optional_string(payload, 'position', max_len=100),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'is_primary': bool(payload.get('is_primary', False)),
    }


def validate_patch_contact(payload):
    ensure_dict(payload)
    cleaned = {}
    if 'first_name' in payload:
        cleaned['first_name'] = require_string(payload, 'first_name', max_len=100)
    if 'last_name' in payload:
        cleaned['last_name'] = optional_string(payload, 'last_name', max_len=100)
    if 'position' in payload:
        cleaned['position'] = optional_string(payload, 'position', max_len=100)
    if 'email' in payload:
        cleaned['email'] = optional_string(payload, 'email', max_len=150)
    if 'phone' in payload:
        cleaned['phone'] = optional_string(payload, 'phone', max_len=50)
    if 'is_primary' in payload:
        cleaned['is_primary'] = bool(payload['is_primary'])
    return cleaned