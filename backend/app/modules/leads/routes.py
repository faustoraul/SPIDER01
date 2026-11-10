from flask import Blueprint, jsonify, request

from . import services
from .schemas import (
    validate_create_lead,
    validate_update_lead,
    validate_patch_lead,
    validate_create_activity,
    validate_public_lead,
)
from ..companies import services as company_services


# ---------- Blueprint interno (requiere company_id en la ruta) ----------

leads_bp = Blueprint(
    'leads',
    __name__,
    url_prefix='/api/companies/<int:company_id>/leads',
)


@leads_bp.route('', methods=['GET'])
def list_leads(company_id):
    company_services.get_company(company_id)

    search = request.args.get('search', type=str)
    status = request.args.get('status', type=str)
    source = request.args.get('source', type=str)
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')

    items = services.list_leads(
        company_id, search=search, status=status,
        source=source, include_inactive=include_inactive,
    )
    return jsonify({
        'items': [l.to_dict() for l in items],
        'total': len(items),
    }), 200


@leads_bp.route('', methods=['POST'])
def create_lead(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    cleaned = validate_create_lead(payload)
    lead = services.create_lead(company_id, cleaned)
    return jsonify(lead.to_dict()), 201


@leads_bp.route('/<int:lead_id>', methods=['GET'])
def get_lead(company_id, lead_id):
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')
    lead = services.get_lead(company_id, lead_id, include_inactive=include_inactive)
    return jsonify(lead.to_dict(include_activities=True)), 200


@leads_bp.route('/<int:lead_id>', methods=['PUT'])
def update_lead(company_id, lead_id):
    payload = request.get_json(silent=True)
    cleaned = validate_update_lead(payload)
    lead = services.update_lead(company_id, lead_id, cleaned)
    return jsonify(lead.to_dict()), 200


@leads_bp.route('/<int:lead_id>', methods=['PATCH'])
def patch_lead(company_id, lead_id):
    payload = request.get_json(silent=True)
    cleaned = validate_patch_lead(payload)
    lead = services.patch_lead(company_id, lead_id, cleaned)
    return jsonify(lead.to_dict()), 200


@leads_bp.route('/<int:lead_id>', methods=['DELETE'])
def delete_lead(company_id, lead_id):
    services.soft_delete_lead(company_id, lead_id)
    return '', 204


@leads_bp.route('/<int:lead_id>/activities', methods=['POST'])
def add_activity(company_id, lead_id):
    payload = request.get_json(silent=True)
    cleaned = validate_create_activity(payload)
    activity = services.add_activity(company_id, lead_id, cleaned)
    return jsonify(activity.to_dict()), 201


@leads_bp.route('/<int:lead_id>/convert', methods=['POST'])
def convert_lead(company_id, lead_id):
    lead, customer = services.convert_to_customer(company_id, lead_id)
    return jsonify({
        'lead': lead.to_dict(),
        'customer': customer.to_dict(),
    }), 200


# ---------- Blueprint público (captación desde formularios externos) ----------

public_leads_bp = Blueprint(
    'public_leads',
    __name__,
    url_prefix='/api/public/companies/<int:company_id>/leads',
)


@public_leads_bp.route('', methods=['POST'])
def create_public_lead(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    cleaned = validate_public_lead(payload)
    lead = services.create_public_lead(company_id, cleaned)
    return jsonify({'ok': True, 'lead_id': lead.id}), 201