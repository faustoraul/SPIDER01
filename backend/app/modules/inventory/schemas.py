from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError
from .models import MOVEMENT_TYPES


def _validate_decimal(value, field, allow_zero=True):
    if value is None:
        return 0.0
    try:
        num = float(value)
        if num < 0 or (not allow_zero and num == 0):
            raise ValidationError(f"El campo '{field}' debe ser mayor o igual a cero.")
        return num
    except (ValueError, TypeError):
        raise ValidationError(f"El campo '{field}' debe ser un número válido.")


def validate_create_category(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=100),
        'description': optional_string(payload, 'description', max_len=255),
    }


def validate_create_brand(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=100),
    }


def validate_create_product(payload):
    ensure_dict(payload)
    return {
        'category_id': payload.get('category_id'),
        'brand_id': payload.get('brand_id'),
        'sku': require_string(payload, 'sku', max_len=100),
        'barcode': optional_string(payload, 'barcode', max_len=100),
        'name': require_string(payload, 'name', max_len=200),
        'description': optional_string(payload, 'description', max_len=1000),
        'unit_measure': optional_string(payload, 'unit_measure', max_len=50) or 'unit',
        'cost_price': _validate_decimal(payload.get('cost_price'), 'cost_price'),
        'sale_price': _validate_decimal(payload.get('sale_price'), 'sale_price'),
        'tax_rate': _validate_decimal(payload.get('tax_rate'), 'tax_rate'),
        'min_stock_alert': int(payload.get('min_stock_alert', 0)),
    }


def validate_movement(payload):
    ensure_dict(payload)
    
    m_type = payload.get('movement_type')
    if m_type not in MOVEMENT_TYPES:
        raise ValidationError(f"movement_type debe ser uno de: {', '.join(MOVEMENT_TYPES)}.")

    qty = _validate_decimal(payload.get('quantity'), 'quantity', allow_zero=False)

    return {
        'branch_id': int(payload.get('branch_id', 0)),
        'product_id': int(payload.get('product_id', 0)),
        'movement_type': m_type,
        'quantity': qty,
        'reference': optional_string(payload, 'reference', max_len=100),
        'notes': optional_string(payload, 'notes', max_len=500),
        'created_by': optional_string(payload, 'created_by', max_len=150),
    }