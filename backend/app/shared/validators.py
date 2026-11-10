from ..core.exceptions import ValidationError


def ensure_dict(payload):
    if not isinstance(payload, dict):
        raise ValidationError('El cuerpo de la solicitud debe ser un objeto JSON.')
    return payload


def require_string(payload, field, min_len=1, max_len=255):
    value = payload.get(field)
    if not isinstance(value, str):
        raise ValidationError(f"El campo '{field}' es obligatorio y debe ser texto.")
    value = value.strip()
    if len(value) < min_len:
        raise ValidationError(f"El campo '{field}' debe tener al menos {min_len} caracteres.")
    if len(value) > max_len:
        raise ValidationError(f"El campo '{field}' no puede exceder {max_len} caracteres.")
    return value


def optional_string(payload, field, max_len=255):
    value = payload.get(field)
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValidationError(f"El campo '{field}' debe ser texto.")
    value = value.strip()
    if len(value) > max_len:
        raise ValidationError(f"El campo '{field}' no puede exceder {max_len} caracteres.")
    return value or None