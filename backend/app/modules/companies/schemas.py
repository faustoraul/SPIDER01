from ...shared.validators import ensure_dict, require_string, optional_string


def validate_create_payload(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'tax_id': optional_string(payload, 'tax_id', max_len=50),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'address': optional_string(payload, 'address', max_len=500),
    }