from flask import Blueprint, jsonify, request
from . import services
from .schemas import validate_create_supplier, validate_create_order, validate_patch_order
from ..companies import services as company_services

purchases_bp = Blueprint(
    'purchases',
    __name__,
    url_prefix='/api/companies/<int:company_id>',
)

# ---------- Proveedores ----------
@purchases_bp.route('/suppliers', methods=['GET', 'POST'])
def suppliers(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        return jsonify([s.to_dict() for s in services.list_suppliers(company_id)]), 200
    else:
        cleaned = validate_create_supplier(request.get_json(silent=True))
        supplier = services.create_supplier(company_id, cleaned)
        return jsonify(supplier.to_dict()), 201

# ---------- Órdenes de Compra ----------
@purchases_bp.route('/purchase-orders', methods=['GET', 'POST'])
def purchase_orders(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        status = request.args.get('status')
        orders = services.list_orders(company_id, status=status)
        return jsonify({'items': [o.to_dict() for o in orders], 'total': len(orders)}), 200
    else:
        cleaned = validate_create_order(request.get_json(silent=True))
        order = services.create_order(company_id, cleaned)
        return jsonify(order.to_dict(include_items=True)), 201

@purchases_bp.route('/purchase-orders/<int:order_id>', methods=['GET', 'PATCH'])
def purchase_order_detail(company_id, order_id):
    if request.method == 'GET':
        order = services.get_order(company_id, order_id)
        return jsonify(order.to_dict(include_items=True)), 200
    else:
        cleaned = validate_patch_order(request.get_json(silent=True))
        order = services.patch_order(company_id, order_id, cleaned)
        return jsonify(order.to_dict(include_items=True)), 200

@purchases_bp.route('/purchase-orders/<int:order_id>/receive', methods=['POST'])
def receive_purchase_order(company_id, order_id):
    """Acción explícita para recibir la orden y actualizar el inventario."""
    order = services.receive_order(company_id, order_id)
    return jsonify(order.to_dict(include_items=True)), 200