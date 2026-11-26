from flask import Blueprint, jsonify, request
from . import services
from .schemas import (
    validate_create_sale, validate_open_cash_session, 
    validate_close_cash_session, validate_create_cash_register
)
from ..companies import services as company_services

sales_bp = Blueprint('sales', __name__, url_prefix='/api/companies/<int:company_id>')

# ---------- Cajas ----------
@sales_bp.route('/cash-registers', methods=['GET', 'POST'])
def cash_registers(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        return jsonify([r.to_dict() for r in services.list_cash_registers(company_id)]), 200
    else:
        cleaned = validate_create_cash_register(request.get_json(silent=True))
        reg = services.create_cash_register(company_id, cleaned)
        return jsonify(reg.to_dict()), 201

# ---------- Turnos de Caja ----------
@sales_bp.route('/cash-sessions', methods=['GET', 'POST'])
def cash_sessions(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        status = request.args.get('status')
        sessions = services.list_sessions(company_id, status)
        return jsonify({'items': [s.to_dict() for s in sessions], 'total': len(sessions)}), 200
    else:
        cleaned = validate_open_cash_session(request.get_json(silent=True))
        session = services.open_session(company_id, cleaned)
        return jsonify(session.to_dict()), 201

@sales_bp.route('/cash-sessions/<int:session_id>/close', methods=['POST'])
def close_cash_session(company_id, session_id):
    cleaned = validate_close_cash_session(request.get_json(silent=True))
    session = services.close_session(company_id, session_id, cleaned)
    return jsonify(session.to_dict()), 200

# ---------- Ventas ----------
@sales_bp.route('/sales', methods=['GET', 'POST'])
def sales(company_id):
    company_services.get_company(company_id)
    if request.method == 'GET':
        status = request.args.get('status')
        sales_list = services.list_sales(company_id, status)
        return jsonify({'items': [s.to_dict() for s in sales_list], 'total': len(sales_list)}), 200
    else:
        cleaned = validate_create_sale(request.get_json(silent=True))
        sale = services.create_sale(company_id, cleaned)
        return jsonify(sale.to_dict(include_items=True)), 201

@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(company_id, sale_id):
    sale = services.get_sale(company_id, sale_id)
    return jsonify(sale.to_dict(include_items=True)), 200