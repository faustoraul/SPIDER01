from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError
from .models import Company


def list_companies():
    return Company.query.order_by(Company.id.asc()).all()


def get_company(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        raise NotFoundError(f'Empresa con id {company_id} no encontrada.')
    return company


def create_company(data):
    if data.get('tax_id'):
        existing = Company.query.filter_by(tax_id=data['tax_id']).first()
        if existing:
            raise ConflictError(f"Ya existe una empresa con tax_id '{data['tax_id']}'.")

    company = Company(
        name=data['name'],
        tax_id=data.get('tax_id'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
    )
    db.session.add(company)
    db.session.commit()
    return company