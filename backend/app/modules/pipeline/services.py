from ...extensions import db
from ...core.exceptions import NotFoundError, ConflictError, ValidationError
from .models import PipelineStage, Opportunity
from ..crm.models import Customer


# ---------- Stages ----------

def list_stages(company_id):
    return PipelineStage.query.filter_by(
        company_id=company_id, is_active=True
    ).order_by(PipelineStage.order_index.asc()).all()


def get_stage(company_id, stage_id):
    stage = PipelineStage.query.filter_by(id=stage_id, company_id=company_id).first()
    if not stage:
        raise NotFoundError(f'Etapa {stage_id} no encontrada.')
    return stage


def create_stage(company_id, data):
    if PipelineStage.query.filter_by(company_id=company_id, code=data['code']).first():
        raise ConflictError(f"Ya existe una etapa con el código '{data['code']}'.")
    
    stage = PipelineStage(company_id=company_id, **data)
    db.session.add(stage)
    db.session.commit()
    return stage


# ---------- Opportunities ----------

def _verify_relations(company_id, customer_id, stage_id):
    """Verifica que el cliente y la etapa existan y pertenezcan a la empresa actual."""
    customer = Customer.query.filter_by(id=customer_id, company_id=company_id).first()
    if not customer:
        raise ValidationError(f"El cliente {customer_id} no existe o no pertenece a esta empresa.")
        
    stage = PipelineStage.query.filter_by(id=stage_id, company_id=company_id).first()
    if not stage:
        raise ValidationError(f"La etapa {stage_id} no existe o no pertenece a esta empresa.")


def list_opportunities(company_id, search=None, stage_id=None, customer_id=None, include_inactive=False):
    query = Opportunity.query.filter_by(company_id=company_id)

    if not include_inactive:
        query = query.filter_by(is_active=True)
    if stage_id:
        query = query.filter_by(stage_id=stage_id)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if search:
        like = f'%{search.strip()}%'
        query = query.filter(Opportunity.name.ilike(like))

    return query.order_by(Opportunity.id.desc()).all()


def get_opportunity(company_id, opp_id, include_inactive=False):
    opp = Opportunity.query.filter_by(id=opp_id, company_id=company_id).first()
    if not opp:
        raise NotFoundError(f'Oportunidad {opp_id} no encontrada.')
    if not opp.is_active and not include_inactive:
        raise NotFoundError(f'Oportunidad {opp_id} no encontrada.')
    return opp


def create_opportunity(company_id, data):
    _verify_relations(company_id, data['customer_id'], data['stage_id'])
    
    opp = Opportunity(company_id=company_id, **data)
    db.session.add(opp)
    db.session.commit()
    return opp


def update_opportunity(company_id, opp_id, data):
    opp = get_opportunity(company_id, opp_id)
    _verify_relations(company_id, data['customer_id'], data['stage_id'])
    
    for key, value in data.items():
        setattr(opp, key, value)
        
    db.session.commit()
    return opp


def patch_opportunity(company_id, opp_id, data):
    opp = get_opportunity(company_id, opp_id)
    
    if 'customer_id' in data or 'stage_id' in data:
        cid = data.get('customer_id', opp.customer_id)
        sid = data.get('stage_id', opp.stage_id)
        _verify_relations(company_id, cid, sid)

    for key, value in data.items():
        setattr(opp, key, value)
        
    db.session.commit()
    return opp


def soft_delete_opportunity(company_id, opp_id):
    opp = get_opportunity(company_id, opp_id)
    opp.is_active = False
    db.session.commit()
    return opp