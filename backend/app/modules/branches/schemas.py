from ...shared.validators import ensure_dict, require_string, optional_string


def validate_create_payload(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'code': require_string(payload, 'code', max_len=50),
        'address': optional_string(payload, 'address', max_len=500),
        'phone': optional_string(payload, 'phone', max_len=50),
    }