from datetime import date
from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError


def _validate_date(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValidationError("La fecha (expected_close_date) debe ser un texto en formato YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError("Formato de fecha inválido. Usa YYYY-MM-DD.")


def _validate_amount(value):
    if value is None:
        return 0.0
    try:
        amount = float(value)
        if amount < 0:
            raise ValidationError("El monto no puede ser negativo.")
        return amount
    except (ValueError, TypeError):
        raise ValidationError("El monto debe ser un número válido.")


def validate_create_opportunity(payload):
    ensure_dict(payload)
    
    customer_id = payload.get('customer_id')
    if not customer_id or not isinstance(customer_id, int):
        raise ValidationError("customer_id es obligatorio y debe ser un entero.")
        
    stage_id = payload.get('stage_id')
    if not stage_id or not isinstance(stage_id, int):
        raise ValidationError("stage_id es obligatorio y debe ser un entero.")

    return {
        'customer_id': customer_id,
        'stage_id': stage_id,
        'name': require_string(payload, 'name', max_len=200),
        'amount': _validate_amount(payload.get('amount')),
        'expected_close_date': _validate_date(payload.get('expected_close_date')),
        'notes': optional_string(payload, 'notes', max_len=1000),
    }


def validate_update_opportunity(payload):
    ensure_dict(payload)
    
    customer_id = payload.get('customer_id')
    if not customer_id or not isinstance(customer_id, int):
        raise ValidationError("customer_id es obligatorio y debe ser un entero.")
        
    stage_id = payload.get('stage_id')
    if not stage_id or not isinstance(stage_id, int):
        raise ValidationError("stage_id es obligatorio y debe ser un entero.")

    return {
        'customer_id': customer_id,
        'stage_id': stage_id,
        'name': require_string(payload, 'name', max_len=200),
        'amount': _validate_amount(payload.get('amount')),
        'expected_close_date': _validate_date(payload.get('expected_close_date')),
        'notes': optional_string(payload, 'notes', max_len=1000),
    }


def validate_patch_opportunity(payload):
    ensure_dict(payload)
    cleaned = {}
    
    if 'customer_id' in payload:
        if not isinstance(payload['customer_id'], int):
            raise ValidationError("customer_id debe ser un entero.")
        cleaned['customer_id'] = payload['customer_id']
        
    if 'stage_id' in payload:
        if not isinstance(payload['stage_id'], int):
            raise ValidationError("stage_id debe ser un entero.")
        cleaned['stage_id'] = payload['stage_id']
        
    if 'name' in payload:
        cleaned['name'] = require_string(payload, 'name', max_len=200)
        
    if 'amount' in payload:
        cleaned['amount'] = _validate_amount(payload['amount'])
        
    if 'expected_close_date' in payload:
        cleaned['expected_close_date'] = _validate_date(payload['expected_close_date'])
        
    if 'notes' in payload:
        cleaned['notes'] = optional_string(payload, 'notes', max_len=1000)

    return cleaned