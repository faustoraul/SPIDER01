from flask import Blueprint, jsonify, request
from . import services
from .schemas import (
    validate_create_opportunity,
    validate_update_opportunity,
    validate_patch_opportunity,
)
from ..companies import services as company_services

pipeline_bp = Blueprint(
    'pipeline',
    __name__,
    url_prefix='/api/companies/<int:company_id>/pipeline',
)

# ---------- Stages ----------

@pipeline_bp.route('/stages', methods=['GET'])
def list_stages(company_id):
    company_services.get_company(company_id)
    stages = services.list_stages(company_id)
    return jsonify([s.to_dict() for s in stages]), 200


@pipeline_bp.route('/stages', methods=['POST'])
def create_stage(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'error': 'validation_error', 'message': 'JSON requerido'}), 422
    
    # Validación simple para el seed/creación manual
    if 'name' not in payload or 'code' not in payload:
        return jsonify({'error': 'validation_error', 'message': 'name y code son requeridos'}), 422
        
    stage = services.create_stage(company_id, {
        'name': payload['name'],
        'code': payload['code'],
        'order_index': payload.get('order_index', 0)
    })
    return jsonify(stage.to_dict()), 201


# ---------- Opportunities ----------

@pipeline_bp.route('/opportunities', methods=['GET'])
def list_opportunities(company_id):
    company_services.get_company(company_id)
    search = request.args.get('search')
    stage_id = request.args.get('stage_id', type=int)
    customer_id = request.args.get('customer_id', type=int)
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')

    opps = services.list_opportunities(
        company_id, search=search, stage_id=stage_id,
        customer_id=customer_id, include_inactive=include_inactive
    )
    return jsonify({
        'items': [o.to_dict() for o in opps],
        'total': len(opps),
    }), 200


@pipeline_bp.route('/opportunities', methods=['POST'])
def create_opportunity(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    cleaned = validate_create_opportunity(payload)
    opp = services.create_opportunity(company_id, cleaned)
    return jsonify(opp.to_dict()), 201


@pipeline_bp.route('/opportunities/<int:opp_id>', methods=['GET'])
def get_opportunity(company_id, opp_id):
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')
    opp = services.get_opportunity(company_id, opp_id, include_inactive=include_inactive)
    return jsonify(opp.to_dict()), 200


@pipeline_bp.route('/opportunities/<int:opp_id>', methods=['PUT'])
def update_opportunity(company_id, opp_id):
    payload = request.get_json(silent=True)
    cleaned = validate_update_opportunity(payload)
    opp = services.update_opportunity(company_id, opp_id, cleaned)
    return jsonify(opp.to_dict()), 200


@pipeline_bp.route('/opportunities/<int:opp_id>', methods=['PATCH'])
def patch_opportunity(company_id, opp_id):
    payload = request.get_json(silent=True)
    cleaned = validate_patch_opportunity(payload)
    opp = services.patch_opportunity(company_id, opp_id, cleaned)
    return jsonify(opp.to_dict()), 200


@pipeline_bp.route('/opportunities/<int:opp_id>', methods=['DELETE'])
def delete_opportunity(company_id, opp_id):
    services.soft_delete_opportunity(company_id, opp_id)
    return '', 204