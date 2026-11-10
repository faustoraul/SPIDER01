from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from .models import Lead, LeadActivity


# ---------- Leads ----------

def list_leads(company_id, search=None, status=None, source=None, include_inactive=False):
    query = Lead.query.filter_by(company_id=company_id)

    if not include_inactive:
        query = query.filter_by(is_active=True)
    if status:
        query = query.filter_by(status=status)
    if source:
        query = query.filter_by(source=source)
    if search:
        like = f'%{search.strip()}%'
        query = query.filter(
            db.or_(
                Lead.name.ilike(like),
                Lead.email.ilike(like),
                Lead.phone.ilike(like),
            )
        )

    return query.order_by(Lead.id.asc()).all()


def get_lead(company_id, lead_id, include_inactive=False):
    lead = Lead.query.filter_by(id=lead_id, company_id=company_id).first()
    if not lead:
        raise NotFoundError(f'Lead {lead_id} no encontrado.')
    if not lead.is_active and not include_inactive:
        raise NotFoundError(f'Lead {lead_id} no encontrado.')
    return lead


def create_lead(company_id, data):
    lead = Lead(company_id=company_id, **data)
    db.session.add(lead)
    db.session.commit()
    return lead


def update_lead(company_id, lead_id, data):
    lead = get_lead(company_id, lead_id)
    for key, value in data.items():
        setattr(lead, key, value)
    db.session.commit()
    return lead


def patch_lead(company_id, lead_id, data):
    lead = get_lead(company_id, lead_id)
    for key, value in data.items():
        setattr(lead, key, value)
    db.session.commit()
    return lead


def soft_delete_lead(company_id, lead_id):
    lead = get_lead(company_id, lead_id)
    lead.is_active = False
    db.session.commit()
    return lead


# ---------- Actividades ----------

def list_activities(company_id, lead_id):
    get_lead(company_id, lead_id)
    return (
        LeadActivity.query
        .filter_by(lead_id=lead_id)
        .order_by(LeadActivity.id.asc())
        .all()
    )


def add_activity(company_id, lead_id, data):
    get_lead(company_id, lead_id)
    activity = LeadActivity(lead_id=lead_id, **data)
    db.session.add(activity)
    db.session.commit()
    return activity


# ---------- Conversión a cliente ----------

def convert_to_customer(company_id, lead_id):
    """
    Convierte un lead en Customer. Reglas:
    - Solo si el lead está 'qualified' o 'new'.
    - Si ya está 'converted', no permite reconvertir.
    - Si el email ya existe como cliente en la misma empresa, lo rechaza.
    """
    from ..crm.models import Customer

    lead = get_lead(company_id, lead_id)

    if lead.status == 'converted' or lead.customer_id:
        raise ConflictError('Este lead ya fue convertido a cliente.')

    if lead.status not in ('new', 'contacted', 'qualified'):
        raise ConflictError(
            f"No se puede convertir un lead en estado '{lead.status}'."
        )

    if lead.email:
        existing = Customer.query.filter_by(
            company_id=company_id, email=lead.email
        ).first()
        if existing:
            raise ConflictError(
                f"Ya existe un cliente con email '{lead.email}' en esta empresa."
            )

    customer = Customer(
        company_id=company_id,
        customer_type='individual',
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        notes=f'Convertido desde lead #{lead.id}',
    )
    db.session.add(customer)
    db.session.flush()

    lead.customer_id = customer.id
    lead.status = 'converted'
    db.session.commit()
    return lead, customer


# ---------- Captación pública ----------

def create_public_lead(company_id, data):
    """
    Endpoint público: no requiere auth. Fuerza source='web', status='new'.
    """
    payload = dict(data)
    payload['source'] = 'web'
    payload['status'] = 'new'
    lead = Lead(company_id=company_id, **payload)
    db.session.add(lead)
    db.session.commit()
    return lead