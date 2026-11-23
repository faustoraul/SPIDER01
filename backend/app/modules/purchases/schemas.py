from datetime import date
from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError
from .models import PURCHASE_STATUSES


def _validate_date(value, field):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValidationError(f"El campo '{field}' debe ser un texto en formato YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError(f"Formato de fecha inválido en '{field}'. Usa YYYY-MM-DD.")


def validate_create_supplier(payload):
    ensure_dict(payload)
    return {
        'name': require_string(payload, 'name', max_len=200),
        'tax_id': optional_string(payload, 'tax_id', max_len=50),
        'email': optional_string(payload, 'email', max_len=150),
        'phone': optional_string(payload, 'phone', max_len=50),
        'address': optional_string(payload, 'address', max_len=500),
        'notes': optional_string(payload, 'notes', max_len=1000),
    }


def validate_create_order(payload):
    ensure_dict(payload)

    # Validar cabecera
    supplier_id = payload.get('supplier_id')
    if not supplier_id or not isinstance(supplier_id, int):
        raise ValidationError("supplier_id es obligatorio y debe ser un entero.")

    branch_id = payload.get('branch_id')
    if not branch_id or not isinstance(branch_id, int):
        raise ValidationError("branch_id es obligatorio y debe ser un entero.")

    order_date = _validate_date(payload.get('order_date'), 'order_date')
    if not order_date:
        raise ValidationError("order_date es obligatorio.")

    expected_date = _validate_date(payload.get('expected_date'), 'expected_date')

    order_number = require_string(payload, 'order_number', max_len=50)

    # Validar ítems
    raw_items = payload.get('items')
    if not isinstance(raw_items, list) or len(raw_items) == 0:
        raise ValidationError("La orden debe incluir al menos un ítem (items).")

    cleaned_items = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise ValidationError(f"El ítem {idx+1} no es un objeto JSON válido.")
        
        pid = item.get('product_id')
        if not pid or not isinstance(pid, int):
            raise ValidationError(f"El ítem {idx+1} debe tener un product_id válido.")
            
        try:
            qty = float(item.get('quantity', 0))
            cost = float(item.get('unit_cost', 0))
            if qty <= 0 or cost < 0:
                raise ValidationError(f"El ítem {idx+1} tiene cantidad o costo inválidos.")
        except (ValueError, TypeError):
            raise ValidationError(f"Cantidad o costo inválido en el ítem {idx+1}.")

        cleaned_items.append({
            'product_id': pid,
            'quantity': qty,
            'unit_cost': cost,
        })

    return {
        'supplier_id': supplier_id,
        'branch_id': branch_id,
        'order_number': order_number,
        'order_date': order_date,
        'expected_date': expected_date,
        'notes': optional_string(payload, 'notes', max_len=1000),
        'items': cleaned_items,
    }


def validate_patch_order(payload):
    ensure_dict(payload)
    cleaned = {}
    
    if 'status' in payload:
        s = payload['status']
        if s not in PURCHASE_STATUSES:
            raise ValidationError(f"status debe ser uno de: {', '.join(PURCHASE_STATUSES)}.")
        cleaned['status'] = s
        
    if 'expected_date' in payload:
        cleaned['expected_date'] = _validate_date(payload['expected_date'], 'expected_date')
        
    if 'notes' in payload:
        cleaned['notes'] = optional_string(payload, 'notes', max_len=1000)

    return cleaned