from flask import Blueprint, jsonify, request

from . import services
from .schemas import validate_create_payload

companies_bp = Blueprint('companies', __name__, url_prefix='/api/companies')


@companies_bp.route('', methods=['GET'])
def list_companies():
    companies = services.list_companies()
    return jsonify([c.to_dict() for c in companies]), 200


@companies_bp.route('', methods=['POST'])
def create_company():
    payload = request.get_json(silent=True)
    cleaned = validate_create_payload(payload)
    company = services.create_company(cleaned)
    return jsonify(company.to_dict()), 201


@companies_bp.route('/<int:company_id>', methods=['GET'])
def get_company(company_id):
    company = services.get_company(company_id)
    return jsonify(company.to_dict()), 200