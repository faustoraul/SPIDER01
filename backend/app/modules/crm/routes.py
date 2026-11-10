from flask import Blueprint, jsonify, request

from . import services
from .schemas import (
    validate_create_customer,
    validate_update_customer,
    validate_patch_customer,
    validate_create_contact,
    validate_patch_contact,
)
from ..companies import services as company_services

crm_bp = Blueprint(
    'crm',
    __name__,
    url_prefix='/api/companies/<int:company_id>/customers',
)


# ---------- Customers ----------

@crm_bp.route('', methods=['GET'])
def list_customers(company_id):
    company_services.get_company(company_id)

    search = request.args.get('search', type=str)
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')

    items = services.list_customers(company_id, search=search, include_inactive=include_inactive)
    return jsonify({
        'items': [c.to_dict() for c in items],
        'total': len(items),
    }), 200


@crm_bp.route('', methods=['POST'])
def create_customer(company_id):
    company_services.get_company(company_id)
    payload = request.get_json(silent=True)
    cleaned = validate_create_customer(payload)
    customer = services.create_customer(company_id, cleaned)
    return jsonify(customer.to_dict(include_contacts=True)), 201


@crm_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(company_id, customer_id):
    include_inactive = request.args.get('include_inactive', default='0') in ('1', 'true', 'yes')
    customer = services.get_customer(company_id, customer_id, include_inactive=include_inactive)
    return jsonify(customer.to_dict(include_contacts=True)), 200


@crm_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(company_id, customer_id):
    payload = request.get_json(silent=True)
    cleaned = validate_update_customer(payload)
    customer = services.update_customer(company_id, customer_id, cleaned)
    return jsonify(customer.to_dict(include_contacts=True)), 200


@crm_bp.route('/<int:customer_id>', methods=['PATCH'])
def patch_customer(company_id, customer_id):
    payload = request.get_json(silent=True)
    cleaned = validate_patch_customer(payload)
    customer = services.patch_customer(company_id, customer_id, cleaned)
    return jsonify(customer.to_dict(include_contacts=True)), 200


@crm_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(company_id, customer_id):
    services.soft_delete_customer(company_id, customer_id)
    return '', 204


# ---------- Contacts ----------

@crm_bp.route('/<int:customer_id>/contacts', methods=['POST'])
def add_contact(company_id, customer_id):
    payload = request.get_json(silent=True)
    cleaned = validate_create_contact(payload)
    contact = services.add_contact(company_id, customer_id, cleaned)
    return jsonify(contact.to_dict()), 201


@crm_bp.route('/<int:customer_id>/contacts/<int:contact_id>', methods=['PATCH'])
def patch_contact(company_id, customer_id, contact_id):
    payload = request.get_json(silent=True)
    cleaned = validate_patch_contact(payload)
    contact = services.patch_contact(company_id, customer_id, contact_id, cleaned)
    return jsonify(contact.to_dict()), 200


@crm_bp.route('/<int:customer_id>/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(company_id, customer_id, contact_id):
    services.delete_contact(company_id, customer_id, contact_id)
    return '', 204