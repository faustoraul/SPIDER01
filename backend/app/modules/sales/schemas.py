from datetime import date
from ...shared.validators import ensure_dict, require_string, optional_string
from ...core.exceptions import ValidationError
from .models import SALE_STATUSES, PAYMENT_METHODS


def _validate_date(value, field):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValidationError(f"El campo '{field}' debe ser texto YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError(f"Formato inválido en '{field}'. Usa YYYY-MM-DD.")


def validate_create_sale(payload):
    ensure_dict(payload)

    branch_id = payload.get('branch_id')
    if not branch_id or not isinstance(branch_id, int):
        raise ValidationError("branch_id es obligatorio y debe ser un entero.")

    customer_id = payload.get('customer_id')
    if customer_id is not None and not isinstance(customer_id, int):
        raise ValidationError("customer_id debe ser un entero o null.")

    sale_number = require_string(payload, 'sale_number', max_len=50)

    issue_date = _validate_date(payload.get('issue_date'), 'issue_date')
    if not issue_date:
        raise ValidationError("issue_date es obligatorio.")

    due_date = _validate_date(payload.get('due_date'), 'due_date')

    # Ítems
    raw_items = payload.get('items')
    if not isinstance(raw_items, list) or len(raw_items) == 0:
        raise ValidationError("La venta debe tener al menos un ítem.")

    cleaned_items = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise ValidationError(f"El ítem {idx+1} no es un objeto válido.")

        pid = item.get('product_id')
        if not pid or not isinstance(pid, int):
            raise ValidationError(f"El ítem {idx+1} requiere product_id válido.")

        try:
            qty = float(item.get('quantity', 0))
            price = float(item.get('unit_price', 0))
            tax = float(item.get('tax_rate', 0))
            disc = float(item.get('discount', 0))
        except (ValueError, TypeError):
            raise ValidationError(f"Valores numéricos inválidos en ítem {idx+1}.")

        if qty <= 0 or price < 0:
            raise ValidationError(f"Cantidad/precio inválidos en ítem {idx+1}.")
        if disc < 0:
            raise ValidationError(f"Descuento negativo en ítem {idx+1}.")

        cleaned_items.append({
            'product_id': pid,
            'quantity': qty,
            'unit_price': price,
            'tax_rate': tax,
            'discount': disc,
        })

    # Pagos
    raw_payments = payload.get('payments') or []
    if not isinstance(raw_payments, list):
        raise ValidationError("payments debe ser una lista.")

    cleaned_payments = []
    for idx, p in enumerate(raw_payments):
        if not isinstance(p, dict):
            raise ValidationError(f"El pago {idx+1} no es válido.")
        method = p.get('method')
        if method not in PAYMENT_METHODS:
            raise ValidationError(f"method debe ser uno de: {', '.join(PAYMENT_METHODS)}.")
        try:
            amount = float(p.get('amount', 0))
        except (ValueError, TypeError):
            raise ValidationError(f"Monto inválido en pago {idx+1}.")
        if amount <= 0:
            raise ValidationError(f"El monto del pago {idx+1} debe ser positivo.")
        cleaned_payments.append({
            'method': method,
            'amount': amount,
            'reference': optional_string(p, 'reference', max_len=100),
            'notes': optional_string(p, 'notes', max_len=500),
        })

    return {
        'branch_id': branch_id,
        'customer_id': customer_id,
        'sale_number': sale_number,
        'issue_date': issue_date,
        'due_date': due_date,
        'notes': optional_string(payload, 'notes', max_len=1000),
        'items': cleaned_items,
        'payments': cleaned_payments,
    }


def validate_open_cash_session(payload):
    ensure_dict(payload)

    register_id = payload.get('cash_register_id')
    if not register_id or not isinstance(register_id, int):
        raise ValidationError("cash_register_id es obligatorio.")

    user_name = require_string(payload, 'user_name', max_len=150)

    try:
        opening = float(payload.get('opening_amount', 0))
    except (ValueError, TypeError):
        raise ValidationError("opening_amount inválido.")
    if opening < 0:
        raise ValidationError("opening_amount no puede ser negativo.")

    return {
        'cash_register_id': register_id,
        'user_name': user_name,
        'opening_amount': opening,
    }


def validate_close_cash_session(payload):
    ensure_dict(payload)

    try:
        closing = float(payload.get('closing_amount', 0))
    except (ValueError, TypeError):
        raise ValidationError("closing_amount inválido.")
    if closing < 0:
        raise ValidationError("closing_amount no puede ser negativo.")

    return {
        'closing_amount': closing,
        'notes': optional_string(payload, 'notes', max_len=1000),
    }


def validate_create_cash_register(payload):
    ensure_dict(payload)

    branch_id = payload.get('branch_id')
    if not branch_id or not isinstance(branch_id, int):
        raise ValidationError("branch_id es obligatorio.")

    return {
        'branch_id': branch_id,
        'name': require_string(payload, 'name', max_len=100),
    }