from flask import Blueprint, jsonify, request
from . import services
from .schemas import (
    validate_create_category, validate_create_brand,
    validate_create_product, validate_movement
)
from ..companies import services as company_services

inventory_bp = Blueprint(
    'inventory',
    __name__,
    url_prefix='/api/companies/<int:company_id>',
)

# ---------- Categorías ----------
@inventory_bp.route('/categories', methods=['GET', 'POST'])
def categories(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        return jsonify([c.to_dict() for c in services.list_categories(company_id)]), 200
    else:
        cleaned = validate_create_category(request.get_json(silent=True))
        cat = services.create_category(company_id, cleaned)
        return jsonify(cat.to_dict()), 201

# ---------- Marcas ----------
@inventory_bp.route('/brands', methods=['GET', 'POST'])
def brands(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        return jsonify([b.to_dict() for b in services.list_brands(company_id)]), 200
    else:
        cleaned = validate_create_brand(request.get_json(silent=True))
        brand = services.create_brand(company_id, cleaned)
        return jsonify(brand.to_dict()), 201

# ---------- Productos ----------
@inventory_bp.route('/products', methods=['GET', 'POST'])
def products(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        search = request.args.get('search')
        items = services.list_products(company_id, search)
        return jsonify({'items': [p.to_dict() for p in items], 'total': len(items)}), 200
    else:
        cleaned = validate_create_product(request.get_json(silent=True))
        prod = services.create_product(company_id, cleaned)
        return jsonify(prod.to_dict()), 201

@inventory_bp.route('/products/<int:product_id>', methods=['GET', 'PATCH'])
def product_detail(company_id, product_id):
    if request.method == 'GET':
        prod = services.get_product(company_id, product_id)
        return jsonify(prod.to_dict()), 200
    else:
        # Validación parcial simplificada para PATCH
        payload = request.get_json(silent=True) or {}
        prod = services.patch_product(company_id, product_id, payload)
        return jsonify(prod.to_dict()), 200

# ---------- Inventario (Stock) ----------
@inventory_bp.route('/branches/<int:branch_id>/inventory', methods=['GET'])
def branch_inventory(company_id, branch_id):
    company_services.get_company(company_id)
    stock = services.get_branch_stock(company_id, branch_id)
    return jsonify(stock), 200

# ---------- Movimientos ----------
@inventory_bp.route('/inventory/movements', methods=['POST'])
def create_movement(company_id):
    company_services.get_company(company_id)
    cleaned = validate_movement(request.get_json(silent=True))
    movement = services.register_movement(company_id, cleaned)
    return jsonify(movement.to_dict()), 201