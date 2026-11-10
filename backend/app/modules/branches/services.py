from ...extensions import db
from ...core.exceptions import ConflictError
from .models import Branch


def list_branches(company_id):
    return (
        Branch.query
        .filter_by(company_id=company_id)
        .order_by(Branch.id.asc())
        .all()
    )


def create_branch(company_id, data):
    existing = Branch.query.filter_by(
        company_id=company_id, code=data['code']
    ).first()
    if existing:
        raise ConflictError(
            f"Ya existe una sucursal con código '{data['code']}' en esta empresa."
        )

    branch = Branch(
        company_id=company_id,
        name=data['name'],
        code=data['code'],
        address=data.get('address'),
        phone=data.get('phone'),
    )
    db.session.add(branch)
    db.session.commit()
    return branch