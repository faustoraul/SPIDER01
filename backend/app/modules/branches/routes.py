from flask import Blueprint, jsonify, request

from . import services
from .schemas import validate_create_payload
from ..companies import services as company_services

branches_bp = Blueprint(
    'branches',
    __name__,
    url_prefix='/api/companies/<int:company_id>/branches',
)


@branches_bp.route('', methods=['GET'])
def list_branches(company_id):
    # Si la empresa no existe → 404. La ruta por sí sola no basta:
    # si no se valida, devolvería [] silenciosamente y ocultaría errores.
    company_services.get_company(company_id)
    branches = services.list_branches(company_id)
    return jsonify([b.to_dict() for b in branches]), 200


@branches_bp.route('', methods=['POST'])
def create_branch(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    cleaned = validate_create_payload(payload)
    branch = services.create_branch(company_id, cleaned)
    return jsonify(branch.to_dict()), 201