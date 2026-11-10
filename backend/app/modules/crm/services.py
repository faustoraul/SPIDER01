from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError
from .models import Customer, Contact


# ---------- Customers ----------

def list_customers(company_id, search=None, include_inactive=False):
    query = Customer.query.filter_by(company_id=company_id)

    if not include_inactive:
        query = query.filter_by(is_active=True)

    if search:
        like = f'%{search.strip()}%'
        query = query.filter(
            db.or_(
                Customer.name.ilike(like),
                Customer.identification.ilike(like),
                Customer.email.ilike(like),
            )
        )

    return query.order_by(Customer.id.asc()).all()


def get_customer(company_id, customer_id, include_inactive=False):
    customer = Customer.query.filter_by(
        id=customer_id, company_id=company_id
    ).first()

    if not customer:
        raise NotFoundError(f'Cliente {customer_id} no encontrado.')

    if not customer.is_active and not include_inactive:
        raise NotFoundError(f'Cliente {customer_id} no encontrado.')

    return customer


def _check_uniqueness(company_id, data, exclude_id=None):
    if data.get('identification'):
        q = Customer.query.filter_by(
            company_id=company_id, identification=data['identification']
        )
        if exclude_id:
            q = q.filter(Customer.id != exclude_id)
        if q.first():
            raise ConflictError(
                f"Ya existe un cliente con identificación '{data['identification']}' en esta empresa."
            )

    if data.get('email'):
        q = Customer.query.filter_by(company_id=company_id, email=data['email'])
        if exclude_id:
            q = q.filter(Customer.id != exclude_id)
        if q.first():
            raise ConflictError(
                f"Ya existe un cliente con email '{data['email']}' en esta empresa."
            )


def create_customer(company_id, data):
    _check_uniqueness(company_id, data)
    customer = Customer(company_id=company_id, **data)
    db.session.add(customer)
    db.session.commit()
    return customer


def update_customer(company_id, customer_id, data):
    customer = get_customer(company_id, customer_id)
    _check_uniqueness(company_id, data, exclude_id=customer_id)

    for key, value in data.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer


def patch_customer(company_id, customer_id, data):
    customer = get_customer(company_id, customer_id)
    _check_uniqueness(company_id, data, exclude_id=customer_id)

    for key, value in data.items():
        setattr(customer, key, value)

    db.session.commit()
    return customer


def soft_delete_customer(company_id, customer_id):
    customer = get_customer(company_id, customer_id)
    customer.is_active = False
    db.session.commit()
    return customer


# ---------- Contacts ----------

def _get_contact(company_id, customer_id, contact_id):
    contact = (
        Contact.query
        .join(Customer, Contact.customer_id == Customer.id)
        .filter(
            Customer.company_id == company_id,
            Customer.id == customer_id,
            Contact.id == contact_id,
        )
        .first()
    )
    if not contact:
        raise NotFoundError(f'Contacto {contact_id} no encontrado.')
    return contact


def _demote_primary(customer_id, keep_id=None):
    query = Contact.query.filter_by(customer_id=customer_id, is_primary=True)
    if keep_id:
        query = query.filter(Contact.id != keep_id)
    for c in query.all():
        c.is_primary = False


def add_contact(company_id, customer_id, data):
    get_customer(company_id, customer_id)

    if data.get('is_primary'):
        _demote_primary(customer_id)

    contact = Contact(customer_id=customer_id, **data)
    db.session.add(contact)
    db.session.commit()
    return contact


def patch_contact(company_id, customer_id, contact_id, data):
    contact = _get_contact(company_id, customer_id, contact_id)

    if data.get('is_primary') is True:
        _demote_primary(customer_id, keep_id=contact_id)

    for key, value in data.items():
        setattr(contact, key, value)

    db.session.commit()
    return contact


def delete_contact(company_id, customer_id, contact_id):
    contact = _get_contact(company_id, customer_id, contact_id)
    db.session.delete(contact)
    db.session.commit()