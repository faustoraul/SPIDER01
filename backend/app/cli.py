import click
from datetime import date, timedelta


def register_cli(app):

    @app.cli.command('seed')
    def seed():
        """Crea 2 empresas y 3 sucursales."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.branches.models import Branch

        if Company.query.count() > 0:
            click.echo('La base de datos ya contiene empresas. Abortando.')
            return

        acme = Company(name='Acme SRL', tax_id='101-00001-1', email='info@acme.test')
        globex = Company(name='Globex SA', tax_id='101-00002-2', email='info@globex.test')
        db.session.add_all([acme, globex])
        db.session.flush()

        db.session.add_all([
            Branch(company_id=acme.id, name='Acme Centro', code='CENTRO'),
            Branch(company_id=acme.id, name='Acme Norte', code='NORTE'),
            Branch(company_id=globex.id, name='Globex Principal', code='PRINC'),
        ])
        db.session.commit()
        click.echo('Datos de prueba creados.')

    @app.cli.command('seed-crm')
    def seed_crm():
        """Crea clientes y contactos."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.crm.models import Customer, Contact

        acme = Company.query.filter_by(name='Acme SRL').first()
        globex = Company.query.filter_by(name='Globex SA').first()
        if not acme or not globex:
            click.echo('Error: primero ejecuta "flask seed".')
            return

        if Customer.query.count() > 0:
            click.echo('Ya existen clientes. Abortando.')
            return

        juan = Customer(company_id=acme.id, customer_type='individual',
                        identification='001-1234567-8', name='Juan Pérez',
                        email='juan@example.test', phone='809-555-0101')
        transportes = Customer(company_id=acme.id, customer_type='company',
                               identification='101-12345-6', name='Transportes del Norte SRL',
                               email='contacto@tn.test', phone='809-555-0202')
        maria = Customer(company_id=globex.id, customer_type='individual',
                         identification='001-9876543-2', name='María López',
                         email='maria@example.test', phone='809-555-0303')

        db.session.add_all([juan, transportes, maria])
        db.session.flush()

        db.session.add_all([
            Contact(customer_id=transportes.id, first_name='Pedro', last_name='Ramírez',
                    position='Gerente General', email='pedro@tn.test',
                    phone='809-555-0203', is_primary=True),
            Contact(customer_id=transportes.id, first_name='Ana', last_name='Torres',
                    position='Compras', email='ana@tn.test', phone='809-555-0204'),
        ])
        db.session.commit()
        click.echo('Clientes y contactos de prueba creados.')

    @app.cli.command('seed-leads')
    def seed_leads():
        """Crea leads de prueba."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.leads.models import Lead, LeadActivity

        acme = Company.query.filter_by(name='Acme SRL').first()
        globex = Company.query.filter_by(name='Globex SA').first()
        if not acme or not globex:
            click.echo('Error: primero ejecuta "flask seed".')
            return

        if Lead.query.count() > 0:
            click.echo('Ya existen leads. Abortando.')
            return

        leads = [
            Lead(company_id=acme.id, name='Carlos Gómez', email='carlos@test.local',
                 phone='809-555-1001', source='facebook', status='new'),
            Lead(company_id=acme.id, name='Laura Méndez', email='laura@test.local',
                 phone='809-555-1002', source='web', status='contacted'),
            Lead(company_id=acme.id, name='Roberto Díaz', email='roberto@test.local',
                 phone='809-555-1003', source='whatsapp', status='qualified'),
            Lead(company_id=globex.id, name='Sofía Castillo', email='sofia@test.local',
                 phone='809-555-2001', source='instagram', status='new'),
        ]
        db.session.add_all(leads)
        db.session.flush()

        db.session.add_all([
            LeadActivity(lead_id=leads[1].id, activity_type='call',
                         notes='Llamada inicial'),
            LeadActivity(lead_id=leads[2].id, activity_type='meeting',
                         notes='Reunión en oficina'),
        ])
        db.session.commit()
        click.echo('Leads de prueba creados.')

    @app.cli.command('seed-pipeline')
    def seed_pipeline():
        """Crea etapas y oportunidades de prueba."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.crm.models import Customer
        from .modules.pipeline.models import PipelineStage, Opportunity, STAGES

        acme = Company.query.filter_by(name='Acme SRL').first()
        globex = Company.query.filter_by(name='Globex SA').first()
        if not acme or not globex:
            click.echo('Error: primero ejecuta "flask seed".')
            return

        if PipelineStage.query.count() > 0:
            click.echo('Ya existen etapas. Abortando.')
            return

        acme_stages = {}
        for code, name, order in STAGES:
            stage = PipelineStage(company_id=acme.id, name=name, code=code, order_index=order)
            db.session.add(stage)
            acme_stages[code] = stage

        for code, name, order in STAGES:
            stage = PipelineStage(company_id=globex.id, name=name, code=code, order_index=order)
            db.session.add(stage)

        db.session.flush()

        juan = Customer.query.filter_by(company_id=acme.id, name='Juan Pérez').first()
        transportes = Customer.query.filter_by(company_id=acme.id, name='Transportes del Norte SRL').first()

        if juan and transportes:
            today = date.today()
            db.session.add_all([
                Opportunity(
                    company_id=acme.id, customer_id=juan.id, stage_id=acme_stages['prospecting'].id,
                    name='Licencia Anual CRM', amount=1500.00,
                    expected_close_date=today + timedelta(days=30),
                    notes='Cliente interesado en la versión Pro.'
                ),
                Opportunity(
                    company_id=acme.id, customer_id=transportes.id, stage_id=acme_stages['proposal'].id,
                    name='Flota de 50 licencias', amount=7500.00,
                    expected_close_date=today + timedelta(days=15),
                    notes='Propuesta enviada.'
                ),
            ])

        db.session.commit()
        click.echo('Pipeline de prueba creado.')

    @app.cli.command('seed-social')
    def seed_social():
        """Crea cuentas sociales de prueba."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.social_media.models import SocialAccount

        acme = Company.query.filter_by(name='Acme SRL').first()
        if not acme:
            click.echo('Error: primero ejecuta "flask seed".')
            return

        if SocialAccount.query.count() > 0:
            click.echo('Ya existen cuentas sociales. Abortando.')
            return

        db.session.add_all([
            SocialAccount(company_id=acme.id, provider='facebook',
                          external_account_id='fb-page-001', access_token='fake-token-fb'),
            SocialAccount(company_id=acme.id, provider='whatsapp',
                          external_account_id='wa-biz-001', access_token='fake-token-wa'),
        ])
        db.session.commit()
        click.echo('Cuentas sociales de prueba creadas.')

    @app.cli.command('seed-inventory')
    def seed_inventory():
        """Crea categorías, marcas, productos y stock inicial."""
        from .extensions import db
        from .modules.companies.models import Company
        from .modules.branches.models import Branch
        from .modules.inventory.models import Category, Brand, Product, Inventory

        acme = Company.query.filter_by(name='Acme SRL').first()
        if not acme:
            click.echo('Error: primero ejecuta "flask seed".')
            return

        if Product.query.count() > 0:
            click.echo('Ya existen productos. Abortando.')
            return

        cat_elec = Category(company_id=acme.id, name='Electrónica')
        cat_ropa = Category(company_id=acme.id, name='Ropa')
        brand_sony = Brand(company_id=acme.id, name='Sony')
        brand_nike = Brand(company_id=acme.id, name='Nike')
        db.session.add_all([cat_elec, cat_ropa, brand_sony, brand_nike])
        db.session.flush()

        p1 = Product(company_id=acme.id, category_id=cat_elec.id, brand_id=brand_sony.id,
                     sku='ELEC-001', name='Laptop Sony VAIO',
                     cost_price=800, sale_price=1200, tax_rate=18, min_stock_alert=5)
        p2 = Product(company_id=acme.id, category_id=cat_ropa.id, brand_id=brand_nike.id,
                     sku='ROPA-001', name='Zapatillas Nike Air',
                     cost_price=50, sale_price=90, tax_rate=18, min_stock_alert=10)
        db.session.add_all([p1, p2])
        db.session.flush()

        branch = Branch.query.filter_by(company_id=acme.id).first()
        if branch:
            inv1 = Inventory(company_id=acme.id, branch_id=branch.id, product_id=p1.id, quantity=20)
            inv2 = Inventory(company_id=acme.id, branch_id=branch.id, product_id=p2.id, quantity=5)
            db.session.add_all([inv1, inv2])

        db.session.commit()
        click.echo('Catálogo e inventario de prueba creados.')